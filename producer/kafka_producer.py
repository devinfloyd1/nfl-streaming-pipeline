"""
Kafka Producer - NFL Play-by-Play Streaming
============================================
Streams historical NFL play-by-play data through Kafka to simulate real-time games.

This producer reads a game's play sequence from CSV and publishes each play
as a separate message to Kafka, creating a realistic streaming data source.
"""

import json
import time
import sys
from pathlib import Path
from typing import Optional
import argparse

import pandas as pd
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable, KafkaError

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class NFLPlayProducer:
    """
    Kafka producer that streams NFL play-by-play data.

    Architecture:
    - Reads play-by-play data from CSV (one game at a time)
    - Converts each play to JSON message
    - Publishes to Kafka topic with controllable rate
    - Simulates real-time game progression
    """

    def __init__(self,
                 bootstrap_servers: str = "localhost:9093",
                 topic: str = "nfl-plays",
                 play_delay: float = 0.5):
        """
        Initialize the Kafka producer.

        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Kafka topic name
            play_delay: Delay in seconds between plays (simulates real-time)
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.play_delay = play_delay
        self.producer = None

    def connect(self):
        """
        Establish connection to Kafka broker.

        KafkaProducer configuration:
        - value_serializer: Converts Python dict to JSON bytes
        - acks='all': Wait for all replicas to acknowledge (reliability)
        - retries: Automatic retry on transient failures
        - compression_type: Reduce network bandwidth
        """
        print(f"🔌 Connecting to Kafka at {self.bootstrap_servers}...")

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                compression_type='gzip',
                max_in_flight_requests_per_connection=1  # Preserve ordering
            )
            print("✓ Connected to Kafka broker")

        except NoBrokersAvailable:
            print("❌ Error: No Kafka brokers available")
            print("Make sure Kafka is running: docker-compose up -d")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error connecting to Kafka: {e}")
            sys.exit(1)

    def load_game_data(self, csv_path: str) -> pd.DataFrame:
        """
        Load play-by-play data for a single game.

        Args:
            csv_path: Path to game CSV file

        Returns:
            DataFrame with plays sorted chronologically
        """
        print(f"\n📂 Loading game data from {csv_path}...")

        if not Path(csv_path).exists():
            raise FileNotFoundError(f"Game file not found: {csv_path}")

        df = pd.read_csv(csv_path)

        # Sort plays chronologically
        # nflfastR uses 'play_id' which increments through the game
        df = df.sort_values(['game_id', 'play_id']).reset_index(drop=True)

        game_id = df['game_id'].iloc[0]
        home_team = df['home_team'].iloc[0]
        away_team = df['away_team'].iloc[0]

        print(f"✓ Loaded {len(df)} plays")
        print(f"  Game: {away_team} @ {home_team}")
        print(f"  Game ID: {game_id}")

        return df

    def create_play_message(self, play_row: pd.Series, play_number: int) -> dict:
        """
        Convert a play from DataFrame row to Kafka message.

        Message schema includes:
        - Game identification
        - Current score and time
        - Field position and down/distance
        - Play result

        Args:
            play_row: Single row from play-by-play DataFrame
            play_number: Sequential play number (1, 2, 3, ...)

        Returns:
            Dictionary representing the play (will be JSON serialized)
        """
        # Extract key fields, handling missing values
        message = {
            # Game Context
            'game_id': str(play_row.get('game_id', '')),
            'play_id': int(play_row.get('play_id', play_number)),
            'play_number': play_number,

            # Time & Score
            'quarter': int(play_row.get('qtr', 1)),
            'time_remaining': float(play_row.get('game_seconds_remaining', 0)),
            'home_score': int(play_row.get('home_score', 0)),
            'away_score': int(play_row.get('away_score', 0)),

            # Game Situation
            'field_position': float(play_row.get('yardline_100', 50)),
            'down': int(play_row.get('down', 1)) if pd.notna(play_row.get('down')) else None,
            'distance': int(play_row.get('ydstogo', 10)) if pd.notna(play_row.get('ydstogo')) else None,
            'score_differential': float(play_row.get('score_differential', 0)),

            # Play Details
            'play_type': str(play_row.get('play_type', 'unknown')),
            'yards_gained': float(play_row.get('yards_gained', 0)) if pd.notna(play_row.get('yards_gained')) else 0,
            'posteam': str(play_row.get('posteam', '')),
            'defteam': str(play_row.get('defteam', '')),

            # Teams
            'home_team': str(play_row.get('home_team', '')),
            'away_team': str(play_row.get('away_team', '')),

            # Feature Engineering Helper Fields
            'is_home_team': int(play_row.get('is_home_team', 0)),
        }

        return message

    def stream_game(self, game_df: pd.DataFrame, max_plays: Optional[int] = None):
        """
        Stream a game's plays to Kafka topic.

        Simulates real-time game progression by:
        1. Reading each play sequentially
        2. Publishing to Kafka
        3. Waiting before next play (configurable delay)

        Args:
            game_df: DataFrame with game's play-by-play data
            max_plays: Optional limit on number of plays to stream
        """
        home_team = game_df['home_team'].iloc[0]
        away_team = game_df['away_team'].iloc[0]

        plays_to_stream = game_df.head(max_plays) if max_plays else game_df

        print(f"\n🏈 Starting game stream: {away_team} @ {home_team}")
        print(f"📊 Streaming {len(plays_to_stream)} plays to topic '{self.topic}'")
        print(f"⏱️  Delay between plays: {self.play_delay}s")
        print("-" * 60)

        for idx, (_, play) in enumerate(plays_to_stream.iterrows(), start=1):
            # Create message
            message = self.create_play_message(play, idx)

            try:
                # Send to Kafka
                # Key by game_id to ensure all plays from same game go to same partition
                future = self.producer.send(
                    self.topic,
                    key=message['game_id'].encode('utf-8'),
                    value=message
                )

                # Block until message is sent (or timeout)
                record_metadata = future.get(timeout=10)

                # Display progress
                quarter = message['quarter']
                time_min = int(message['time_remaining'] // 60)
                time_sec = int(message['time_remaining'] % 60)
                score_str = f"{message['away_team']} {message['away_score']} - {message['home_score']} {message['home_team']}"

                print(f"Play #{idx:3d} | Q{quarter} {time_min:2d}:{time_sec:02d} | "
                      f"{score_str:20s} | {message['play_type']:15s} | "
                      f"Topic: {record_metadata.topic} Partition: {record_metadata.partition}")

                # Simulate real-time delay
                time.sleep(self.play_delay)

            except KafkaError as e:
                print(f"❌ Error sending play #{idx}: {e}")
                continue

        # Ensure all messages are sent
        self.producer.flush()

        print("-" * 60)
        print(f"✓ Finished streaming {len(plays_to_stream)} plays")

    def close(self):
        """Close Kafka producer connection."""
        if self.producer:
            self.producer.close()
            print("🔌 Producer connection closed")


def main():
    """
    Main execution: Stream NFL game data to Kafka.
    """
    parser = argparse.ArgumentParser(
        description="Stream NFL play-by-play data to Kafka"
    )
    parser.add_argument(
        '--game-file',
        type=str,
        default='data/game_super_bowl_57.csv',
        help='Path to game CSV file'
    )
    parser.add_argument(
        '--kafka-server',
        type=str,
        default='localhost:9093',
        help='Kafka bootstrap server'
    )
    parser.add_argument(
        '--topic',
        type=str,
        default='nfl-plays',
        help='Kafka topic name'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between plays in seconds'
    )
    parser.add_argument(
        '--max-plays',
        type=int,
        default=None,
        help='Maximum number of plays to stream (default: all)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("NFL KAFKA PRODUCER - Play-by-Play Streaming")
    print("=" * 60)

    # Initialize producer
    producer = NFLPlayProducer(
        bootstrap_servers=args.kafka_server,
        topic=args.topic,
        play_delay=args.delay
    )

    try:
        # Connect to Kafka
        producer.connect()

        # Load game data
        game_df = producer.load_game_data(args.game_file)

        # Stream the game
        producer.stream_game(game_df, max_plays=args.max_plays)

    except KeyboardInterrupt:
        print("\n\n⚠️  Stream interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        producer.close()

    print("\n" + "=" * 60)
    print("✓ PRODUCER FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()
