"""
NFL Data Fetching Module
========================
Downloads and processes NFL play-by-play data using the nfl-data-py library.
This module provides free access to nflfastR data for building ML pipelines.

Data Source: nflfastR via nfl-data-py
"""

import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import nfl_data_py as nfl
from tqdm import tqdm

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class NFLDataFetcher:
    """
    Fetches and processes NFL play-by-play data from nflfastR.

    The nflfastR dataset includes every play from NFL games with rich metadata:
    - Game situation (score, time, field position)
    - Play details (type, yards gained, result)
    - Team information (home/away, names, stats)
    - Win probability calculations
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the data fetcher.

        Args:
            data_dir: Directory to store downloaded CSV files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def fetch_season_data(self, years: list[int]) -> pd.DataFrame:
        """
        Download play-by-play data for specified seasons.

        Args:
            years: List of years to download (e.g., [2023, 2024])

        Returns:
            DataFrame with play-by-play data
        """
        print(f"📊 Fetching NFL play-by-play data for seasons: {years}")

        # nfl_data_py.import_pbp_data() fetches play-by-play from nflfastR
        # This is the same data used by professional analytics teams
        df = nfl.import_pbp_data(years=years)

        print(f"✓ Downloaded {len(df):,} plays from {len(df['game_id'].unique())} games")

        return df

    def clean_and_filter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and filter play-by-play data to relevant plays only.

        Excludes:
        - Administrative plays (timeouts, 2-minute warnings)
        - Penalties without actual plays
        - End-of-quarter/game markers
        - Kickoffs (unless returned)

        Args:
            df: Raw play-by-play DataFrame

        Returns:
            Cleaned DataFrame with only action plays
        """
        print("🧹 Cleaning and filtering data...")

        original_count = len(df)

        # Filter to actual plays only (exclude timeouts, penalties, etc.)
        # play_type indicates the action that occurred
        valid_play_types = [
            'pass', 'run', 'punt', 'field_goal',
            'extra_point', 'kickoff', 'qb_kneel', 'qb_spike'
        ]
        df = df[df['play_type'].isin(valid_play_types)].copy()

        # Remove plays with missing critical data
        # These fields are essential for ML feature engineering
        required_columns = [
            'game_id', 'play_id', 'posteam', 'defteam',
            'game_seconds_remaining', 'yardline_100',
            'down', 'ydstogo', 'score_differential',
            'home_score', 'away_score', 'qtr'
        ]

        for col in required_columns:
            df = df[df[col].notna()]

        # Remove garbage time (games decided by >21 points in 4th quarter)
        # This improves model quality by focusing on competitive situations
        df = df[~(
            (df['qtr'] == 4) &
            (df['game_seconds_remaining'] < 600) &
            (df['score_differential'].abs() > 21)
        )]

        # Add useful derived features
        df['is_home_team'] = (df['posteam'] == df['home_team']).astype(int)
        df['field_position'] = df['yardline_100']  # 0 = goal line, 100 = own goal line

        print(f"✓ Filtered from {original_count:,} to {len(df):,} plays")
        print(f"✓ Kept {len(df['game_id'].unique())} games")

        return df

    def save_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """
        Save DataFrame to CSV file.

        Args:
            df: DataFrame to save
            filename: Output filename (without path)

        Returns:
            Full path to saved file
        """
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)

        file_size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"💾 Saved to {filepath} ({file_size_mb:.1f} MB)")

        return str(filepath)

    def get_game_list(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract list of games with metadata.

        Args:
            df: Play-by-play DataFrame

        Returns:
            DataFrame with one row per game
        """
        games = df.groupby('game_id').agg({
            'game_date': 'first',
            'home_team': 'first',
            'away_team': 'first',
            'home_score': 'last',  # Final score
            'away_score': 'last',
            'play_id': 'count'  # Number of plays
        }).reset_index()

        games.columns = ['game_id', 'date', 'home_team', 'away_team',
                        'home_final_score', 'away_final_score', 'num_plays']

        return games

    def export_single_game(self, df: pd.DataFrame, game_id: str,
                          output_file: Optional[str] = None) -> str:
        """
        Export a single game's play-by-play data.

        Useful for testing the streaming pipeline with one game.

        Args:
            df: Full play-by-play DataFrame
            game_id: Game ID to export (e.g., "2023_01_KC_PHI")
            output_file: Optional custom filename

        Returns:
            Path to exported file
        """
        game_df = df[df['game_id'] == game_id].copy()

        if len(game_df) == 0:
            raise ValueError(f"Game {game_id} not found in dataset")

        if output_file is None:
            output_file = f"game_{game_id}.csv"

        filepath = self.save_to_csv(game_df, output_file)

        home = game_df['home_team'].iloc[0]
        away = game_df['away_team'].iloc[0]
        print(f"✓ Exported {len(game_df)} plays from {away} @ {home}")

        return filepath


def main():
    """
    Main execution: Download and prepare NFL data for the streaming pipeline.
    """
    print("=" * 60)
    print("NFL DATA FETCHER - nflfastR Play-by-Play Data")
    print("=" * 60)

    # Initialize fetcher
    fetcher = NFLDataFetcher(data_dir="data")

    # Fetch 2023 season data (most recent complete season)
    # For 2024 season, use [2024] - data available during/after the season
    df = fetcher.fetch_season_data(years=[2023])

    # Clean and filter to relevant plays
    df = fetcher.clean_and_filter_data(df)

    # Save full dataset
    fetcher.save_to_csv(df, "nfl_plays_2023.csv")

    # Get and save game list for easy reference
    games = fetcher.get_game_list(df)
    fetcher.save_to_csv(games, "nfl_games_2023.csv")

    print("\n📋 Sample games available:")
    print(games.head(10).to_string(index=False))

    # Export a few interesting games for testing
    # Super Bowl LVII: KC vs PHI
    try:
        super_bowl = games[
            (games['home_team'] == 'PHI') & (games['away_team'] == 'KC')
        ]['game_id'].iloc[0]

        fetcher.export_single_game(df, super_bowl, "game_super_bowl_57.csv")
        print(f"\n✓ Exported Super Bowl LVII for testing: {super_bowl}")
    except (IndexError, KeyError):
        print("\n⚠ Super Bowl game not found, skipping export")

    print("\n" + "=" * 60)
    print("✓ DATA FETCH COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review data/nfl_games_2023.csv to pick games for streaming")
    print("2. Run models/train_models.py to train ML models")
    print("3. Start Kafka: docker-compose up -d")


if __name__ == "__main__":
    main()
