"""
PySpark Streaming Consumer - Real-Time NFL Predictions
=======================================================
Consumes play-by-play events from Kafka and makes real-time ML predictions:
- Win probability for each team
- Projected final score

This demonstrates production ML serving in a streaming pipeline.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    FloatType, DoubleType
)
import joblib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class MLPredictor:
    """
    Wrapper for ML models to make predictions on streaming data.

    Models are loaded once at initialization and reused for all predictions.
    This is critical for low-latency inference.
    """

    def __init__(self, models_dir: str = "models"):
        """
        Load pre-trained ML models.

        Args:
            models_dir: Directory containing saved model files
        """
        models_path = Path(models_dir)

        print("📦 Loading ML models...")

        self.win_prob_model = joblib.load(models_path / "win_probability_model.pkl")
        self.score_model_home = joblib.load(models_path / "score_model_home.pkl")
        self.score_model_away = joblib.load(models_path / "score_model_away.pkl")
        self.feature_scaler = joblib.load(models_path / "feature_scaler.pkl")
        self.feature_columns = joblib.load(models_path / "feature_columns.pkl")

        print("✓ Models loaded successfully")

    def engineer_features(self, play_data: dict) -> pd.DataFrame:
        """
        Engineer ML features from raw play data.

        This must match the feature engineering in train_models.py.

        Args:
            play_data: Dictionary with play information

        Returns:
            DataFrame with features in correct order
        """
        # Calculate derived features
        score_diff = play_data['score_differential']
        time_remaining = play_data['time_remaining']
        quarter = play_data['quarter']
        field_pos = play_data['field_position']
        down = play_data.get('down', 1) or 1
        distance = play_data.get('distance', 10) or 10

        # Create feature dictionary matching training
        features = {
            'score_differential': score_diff,
            'time_remaining_pct': time_remaining / 3600,
            'quarter': quarter,
            'is_fourth_quarter': 1 if quarter == 4 else 0,
            'field_position_pct': field_pos / 100,
            'down': down,
            'distance': distance,
            'down_distance_ratio': distance / (down + 1),
            'current_home_score': play_data['home_score'],
            'current_away_score': play_data['away_score'],
            'total_points_scored': play_data['home_score'] + play_data['away_score'],
            'is_home_team': play_data['is_home_team'],
            'is_first_half': 1 if quarter <= 2 else 0,
            'is_second_half': 1 if quarter >= 3 else 0,
            'is_close_game': 1 if abs(score_diff) <= 7 else 0,
            'is_blowout': 1 if abs(score_diff) > 21 else 0,
        }

        # Create DataFrame with features in correct order
        df = pd.DataFrame([features])[self.feature_columns]

        return df

    def predict(self, play_data: dict) -> dict:
        """
        Make predictions for current game state.

        Args:
            play_data: Dictionary with play information from Kafka

        Returns:
            Dictionary with predictions
        """
        # Engineer features
        X = self.engineer_features(play_data)

        # Scale features (same transformation as training)
        X_scaled = self.feature_scaler.transform(X)

        # Predict win probability
        # predict_proba returns [prob_away_win, prob_home_win]
        win_probs = self.win_prob_model.predict_proba(X_scaled)[0]
        home_win_prob = win_probs[1]
        away_win_prob = win_probs[0]

        # Predict final scores
        home_score_pred = self.score_model_home.predict(X_scaled)[0]
        away_score_pred = self.score_model_away.predict(X_scaled)[0]

        # Ensure non-negative scores
        home_score_pred = max(0, round(home_score_pred))
        away_score_pred = max(0, round(away_score_pred))

        return {
            'home_win_probability': float(home_win_prob),
            'away_win_probability': float(away_win_prob),
            'predicted_home_score': int(home_score_pred),
            'predicted_away_score': int(away_score_pred)
        }


class NFLSparkConsumer:
    """
    PySpark Streaming consumer for NFL play-by-play predictions.

    Architecture:
    1. Read messages from Kafka using Spark Structured Streaming
    2. Parse JSON play data
    3. Apply ML models to predict outcomes
    4. Output predictions in real-time
    5. Save predictions to CSV for analysis
    """

    def __init__(self,
                 kafka_servers: str = "localhost:9093",
                 kafka_topic: str = "nfl-plays",
                 models_dir: str = "models",
                 output_dir: str = "predictions"):
        """
        Initialize Spark consumer.

        Args:
            kafka_servers: Kafka bootstrap servers
            kafka_topic: Topic to consume from
            models_dir: Directory with trained models
            output_dir: Directory to save predictions
        """
        self.kafka_servers = kafka_servers
        self.kafka_topic = kafka_topic
        self.models_dir = models_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.spark = None
        self.predictor = None

    def initialize_spark(self):
        """
        Create Spark session with Kafka support.

        Spark Structured Streaming provides:
        - Fault tolerance (checkpointing)
        - Exactly-once processing semantics
        - Scalability (can run on cluster)
        """
        print("⚡ Initializing Spark session...")

        self.spark = SparkSession.builder \
            .appName("NFL-ML-Predictions") \
            .config("spark.jars.packages",
                   "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
            .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
            .getOrCreate()

        # Set log level to reduce noise
        self.spark.sparkContext.setLogLevel("WARN")

        print("✓ Spark session created")

    def define_schema(self) -> StructType:
        """
        Define schema for Kafka message parsing.

        This matches the message format from kafka_producer.py.

        Returns:
            StructType schema for from_json()
        """
        return StructType([
            StructField("game_id", StringType(), True),
            StructField("play_id", IntegerType(), True),
            StructField("play_number", IntegerType(), True),
            StructField("quarter", IntegerType(), True),
            StructField("time_remaining", DoubleType(), True),
            StructField("home_score", IntegerType(), True),
            StructField("away_score", IntegerType(), True),
            StructField("field_position", DoubleType(), True),
            StructField("down", IntegerType(), True),
            StructField("distance", IntegerType(), True),
            StructField("score_differential", DoubleType(), True),
            StructField("play_type", StringType(), True),
            StructField("yards_gained", DoubleType(), True),
            StructField("posteam", StringType(), True),
            StructField("defteam", StringType(), True),
            StructField("home_team", StringType(), True),
            StructField("away_team", StringType(), True),
            StructField("is_home_team", IntegerType(), True),
        ])

    def create_kafka_stream(self):
        """
        Create streaming DataFrame from Kafka topic.

        Returns:
            Streaming DataFrame
        """
        print(f"📡 Connecting to Kafka topic '{self.kafka_topic}'...")

        # Read from Kafka
        # startingOffsets="latest" means only read new messages
        kafka_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_servers) \
            .option("subscribe", self.kafka_topic) \
            .option("startingOffsets", "latest") \
            .load()

        # Kafka messages have: key, value, topic, partition, offset, timestamp
        # We need to parse the 'value' field from JSON

        schema = self.define_schema()

        # Parse JSON from Kafka value
        parsed_df = kafka_df.select(
            from_json(col("value").cast("string"), schema).alias("data")
        ).select("data.*")

        print("✓ Kafka stream created")

        return parsed_df

    def process_stream(self):
        """
        Process streaming data with ML predictions.

        This is where the magic happens:
        1. Read plays from Kafka in real-time
        2. Apply ML models to each play
        3. Display predictions
        4. Save to CSV
        """
        # Load ML models
        self.predictor = MLPredictor(self.models_dir)

        # Create streaming DataFrame
        stream_df = self.create_kafka_stream()

        print("\n" + "=" * 80)
        print("🏈 LIVE GAME PREDICTIONS - Streaming Started")
        print("=" * 80)
        print("Format: Play # | Quarter Time | Score | Win Prob | Projected Final")
        print("-" * 80)

        # Define prediction UDF
        # This function will be applied to each row in the stream
        def make_prediction_udf(play_data_row):
            """Convert pandas Series to dict and make prediction."""
            # pandas Series uses .to_dict(), not .asDict() (which is for PySpark Row)
            play_data = play_data_row.to_dict()

            # Make predictions
            predictions = self.predictor.predict(play_data)

            # Format output
            play_num = play_data['play_number']
            quarter = play_data['quarter']
            time_min = int(play_data['time_remaining'] // 60)
            time_sec = int(play_data['time_remaining'] % 60)

            home_team = play_data['home_team']
            away_team = play_data['away_team']
            home_score = play_data['home_score']
            away_score = play_data['away_score']

            home_win_prob = predictions['home_win_probability'] * 100
            away_win_prob = predictions['away_win_probability'] * 100

            pred_home = predictions['predicted_home_score']
            pred_away = predictions['predicted_away_score']

            # Display prediction
            output = (
                f"Play #{play_num:3d} | "
                f"Q{quarter} {time_min:2d}:{time_sec:02d} | "
                f"{away_team} {away_score:2d} - {home_score:2d} {home_team} | "
                f"{home_team} {home_win_prob:5.1f}% win prob | "
                f"Projected: {away_team} {pred_away} - {pred_home} {home_team}"
            )

            print(output)

            # Return row with predictions for CSV output
            return {
                **play_data,
                'home_win_probability': home_win_prob,
                'away_win_probability': away_win_prob,
                'predicted_home_score': pred_home,
                'predicted_away_score': pred_away,
                'timestamp': datetime.now().isoformat()
            }

        # Process each micro-batch
        # foreachBatch allows us to use pandas/sklearn on each batch
        def process_batch(batch_df, batch_id):
            """Process a micro-batch of plays."""
            if batch_df.isEmpty():
                return

            # Convert to Pandas for easier processing
            pdf = batch_df.toPandas()

            # Make predictions for each play
            results = []
            for _, row in pdf.iterrows():
                pred_row = make_prediction_udf(row)
                results.append(pred_row)

            # Save predictions to CSV
            results_df = pd.DataFrame(results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"predictions_{timestamp}_batch_{batch_id}.csv"
            results_df.to_csv(output_file, index=False)

        # Start streaming query
        query = stream_df.writeStream \
            .foreachBatch(process_batch) \
            .outputMode("append") \
            .start()

        # Wait for termination (Ctrl+C to stop)
        query.awaitTermination()

    def stop(self):
        """Stop Spark session."""
        if self.spark:
            self.spark.stop()
            print("\n⚡ Spark session stopped")


def main():
    """
    Main execution: Start Spark consumer for real-time predictions.
    """
    parser = argparse.ArgumentParser(
        description="PySpark consumer for real-time NFL predictions"
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
        '--models-dir',
        type=str,
        default='models',
        help='Directory with trained models'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='predictions',
        help='Directory to save predictions'
    )

    args = parser.parse_args()

    # Verify models exist
    models_path = Path(args.models_dir)
    if not (models_path / "win_probability_model.pkl").exists():
        print("❌ Error: ML models not found")
        print("Run 'python models/train_models.py' first to train models")
        sys.exit(1)

    print("=" * 80)
    print("NFL SPARK CONSUMER - Real-Time ML Predictions")
    print("=" * 80)

    # Initialize consumer
    consumer = NFLSparkConsumer(
        kafka_servers=args.kafka_server,
        kafka_topic=args.topic,
        models_dir=args.models_dir,
        output_dir=args.output_dir
    )

    try:
        # Initialize Spark
        consumer.initialize_spark()

        # Process stream
        consumer.process_stream()

    except KeyboardInterrupt:
        print("\n\n⚠️  Consumer stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        consumer.stop()

    print("\n" + "=" * 80)
    print("✓ CONSUMER FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    main()
