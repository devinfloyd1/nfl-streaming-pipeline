"""
NFL ML Model Training
=====================
Trains machine learning models for real-time game predictions:
1. Win Probability Model (Logistic Regression)
2. Final Score Predictor (Linear Regression)

These models are designed for low-latency inference in streaming pipelines.
"""

import os
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, classification_report, roc_auc_score,
    mean_absolute_error, mean_squared_error, r2_score
)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class NFLModelTrainer:
    """
    Trains and evaluates ML models for NFL game predictions.

    Feature Engineering Philosophy:
    - Use in-game situation features that are available during live play
    - Avoid lookahead bias (don't use future information)
    - Keep features simple for fast, robust inference
    """

    def __init__(self, models_dir: str = "models"):
        """
        Initialize the model trainer.

        Args:
            models_dir: Directory to save trained models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        self.win_prob_model = None
        self.score_model_home = None
        self.score_model_away = None
        self.feature_scaler = None
        self.feature_columns = None

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create ML features from raw play-by-play data.

        Features capture the current game state:
        - Score situation (leading/trailing)
        - Time pressure (quarter, seconds remaining)
        - Field position (closer to opponent's goal = advantage)
        - Down and distance (offensive situation)
        - Home field advantage

        Args:
            df: Raw play-by-play DataFrame

        Returns:
            DataFrame with engineered features
        """
        print("🔧 Engineering features from play-by-play data...")

        df = df.copy()

        # TARGET VARIABLES
        # ==============================================================
        # Win probability target: Did the home team win?
        df['home_team_won'] = (df['home_score'] > df['away_score']).astype(int)

        # Final score targets (for score prediction model)
        df['final_home_score'] = df.groupby('game_id')['home_score'].transform('last')
        df['final_away_score'] = df.groupby('game_id')['away_score'].transform('last')

        # PREDICTOR FEATURES
        # ==============================================================

        # 1. Score Differential (negative = home team trailing)
        # This is the most important feature for win probability
        df['score_differential'] = df['score_differential'].fillna(0)

        # 2. Time Remaining (seconds)
        # More time = more opportunity to change outcome
        df['time_remaining'] = df['game_seconds_remaining']
        df['time_remaining_pct'] = df['time_remaining'] / 3600  # Normalize to [0,1]

        # 3. Quarter (game phase matters)
        df['quarter'] = df['qtr']
        df['is_fourth_quarter'] = (df['quarter'] == 4).astype(int)

        # 4. Field Position (0-100, where 0 = opponent's goal line)
        # Lower number = better field position for offense
        df['field_position'] = df['yardline_100']
        df['field_position_pct'] = df['field_position'] / 100  # Normalize

        # 5. Down & Distance
        # Third/fourth down with long distance = disadvantage
        df['down'] = df['down'].fillna(1)
        df['distance'] = df['ydstogo'].fillna(10)
        df['down_distance_ratio'] = df['distance'] / (df['down'] + 1)

        # 6. Current Score (absolute values)
        df['current_home_score'] = df['home_score']
        df['current_away_score'] = df['away_score']
        df['total_points_scored'] = df['current_home_score'] + df['current_away_score']

        # 7. Home Field Advantage
        df['is_home_team'] = df['is_home_team']

        # 8. Game Phase Features
        df['is_first_half'] = (df['quarter'] <= 2).astype(int)
        df['is_second_half'] = (df['quarter'] >= 3).astype(int)

        # 9. Score Situation Categories
        df['is_close_game'] = (df['score_differential'].abs() <= 7).astype(int)
        df['is_blowout'] = (df['score_differential'].abs() > 21).astype(int)

        # Remove rows with any NaN in key features
        feature_cols = [
            'score_differential', 'time_remaining', 'time_remaining_pct',
            'quarter', 'is_fourth_quarter', 'field_position', 'field_position_pct',
            'down', 'distance', 'down_distance_ratio',
            'current_home_score', 'current_away_score', 'total_points_scored',
            'is_home_team', 'is_first_half', 'is_second_half',
            'is_close_game', 'is_blowout'
        ]

        df = df.dropna(subset=feature_cols)

        print(f"✓ Engineered {len(feature_cols)} features for {len(df):,} plays")

        return df

    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """
        Prepare feature matrix and target variables for training.

        Args:
            df: DataFrame with engineered features

        Returns:
            Tuple of (features, win_target, home_score_target, away_score_target)
        """
        # Define feature columns for models
        self.feature_columns = [
            'score_differential', 'time_remaining_pct',
            'quarter', 'is_fourth_quarter',
            'field_position_pct',
            'down', 'distance', 'down_distance_ratio',
            'current_home_score', 'current_away_score', 'total_points_scored',
            'is_home_team',
            'is_first_half', 'is_second_half',
            'is_close_game', 'is_blowout'
        ]

        X = df[self.feature_columns]
        y_win = df['home_team_won']
        y_home_score = df['final_home_score']
        y_away_score = df['final_away_score']

        return X, y_win, y_home_score, y_away_score

    def train_win_probability_model(self, X: pd.DataFrame, y: pd.Series):
        """
        Train logistic regression model for win probability.

        Logistic Regression is ideal for this task because:
        - Fast inference (critical for real-time streaming)
        - Probabilistic outputs (not just 0/1 predictions)
        - Interpretable coefficients
        - Works well with game situation features

        Args:
            X: Feature matrix
            y: Binary target (1 = home team wins, 0 = away team wins)
        """
        print("\n🎯 Training Win Probability Model (Logistic Regression)...")

        # Split data: 80% train, 20% test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Scale features for better convergence
        # StandardScaler: (x - mean) / std
        self.feature_scaler = StandardScaler()
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_test_scaled = self.feature_scaler.transform(X_test)

        # Train logistic regression with L2 regularization
        # C=1.0 is moderate regularization (prevents overfitting)
        self.win_prob_model = LogisticRegression(
            C=1.0,
            max_iter=1000,
            random_state=42,
            solver='lbfgs'  # Fast solver for medium datasets
        )

        self.win_prob_model.fit(X_train_scaled, y_train)

        # Evaluate model
        y_pred = self.win_prob_model.predict(X_test_scaled)
        y_pred_proba = self.win_prob_model.predict_proba(X_test_scaled)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)

        print(f"✓ Model trained on {len(X_train):,} plays")
        print(f"  Accuracy: {accuracy:.3f}")
        print(f"  ROC-AUC: {auc:.3f}")

        print("\n📊 Classification Report:")
        print(classification_report(y_test, y_pred,
                                   target_names=['Away Win', 'Home Win']))

        # Feature importance (top 5 most important features)
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'coefficient': self.win_prob_model.coef_[0]
        }).sort_values('coefficient', key=abs, ascending=False)

        print("\n🔍 Top 5 Most Important Features:")
        print(feature_importance.head().to_string(index=False))

    def train_score_prediction_models(self, X: pd.DataFrame,
                                     y_home: pd.Series, y_away: pd.Series):
        """
        Train linear regression models for final score prediction.

        We train separate models for home and away scores because:
        - Each team's scoring is influenced differently by game situation
        - Home field advantage affects scoring
        - Allows for asymmetric predictions

        Args:
            X: Feature matrix
            y_home: Home team final score
            y_away: Away team final score
        """
        print("\n📈 Training Final Score Prediction Models (Linear Regression)...")

        # Split data
        X_train, X_test, y_home_train, y_home_test = train_test_split(
            X, y_home, test_size=0.2, random_state=42
        )
        _, _, y_away_train, y_away_test = train_test_split(
            X, y_away, test_size=0.2, random_state=42
        )

        # Use same scaler as win probability model
        X_train_scaled = self.feature_scaler.transform(X_train)
        X_test_scaled = self.feature_scaler.transform(X_test)

        # Train home score model
        self.score_model_home = LinearRegression()
        self.score_model_home.fit(X_train_scaled, y_home_train)

        # Train away score model
        self.score_model_away = LinearRegression()
        self.score_model_away.fit(X_train_scaled, y_away_train)

        # Evaluate home score model
        y_home_pred = self.score_model_home.predict(X_test_scaled)
        mae_home = mean_absolute_error(y_home_test, y_home_pred)
        rmse_home = np.sqrt(mean_squared_error(y_home_test, y_home_pred))
        r2_home = r2_score(y_home_test, y_home_pred)

        print(f"\n✓ Home Score Model:")
        print(f"  MAE: {mae_home:.2f} points")
        print(f"  RMSE: {rmse_home:.2f} points")
        print(f"  R²: {r2_home:.3f}")

        # Evaluate away score model
        y_away_pred = self.score_model_away.predict(X_test_scaled)
        mae_away = mean_absolute_error(y_away_test, y_away_pred)
        rmse_away = np.sqrt(mean_squared_error(y_away_test, y_away_pred))
        r2_away = r2_score(y_away_test, y_away_pred)

        print(f"\n✓ Away Score Model:")
        print(f"  MAE: {mae_away:.2f} points")
        print(f"  RMSE: {rmse_away:.2f} points")
        print(f"  R²: {r2_away:.3f}")

    def save_models(self):
        """
        Save trained models and preprocessing objects to disk.

        Uses joblib for efficient serialization of scikit-learn models.
        """
        print("\n💾 Saving models...")

        # Save models
        joblib.dump(self.win_prob_model,
                   self.models_dir / "win_probability_model.pkl")
        joblib.dump(self.score_model_home,
                   self.models_dir / "score_model_home.pkl")
        joblib.dump(self.score_model_away,
                   self.models_dir / "score_model_away.pkl")

        # Save preprocessing objects
        joblib.dump(self.feature_scaler,
                   self.models_dir / "feature_scaler.pkl")
        joblib.dump(self.feature_columns,
                   self.models_dir / "feature_columns.pkl")

        print(f"✓ Models saved to {self.models_dir}/")

    @staticmethod
    def load_models(models_dir: str = "models"):
        """
        Load trained models from disk.

        Returns:
            Dictionary with models and preprocessing objects
        """
        models_path = Path(models_dir)

        return {
            'win_prob_model': joblib.load(models_path / "win_probability_model.pkl"),
            'score_model_home': joblib.load(models_path / "score_model_home.pkl"),
            'score_model_away': joblib.load(models_path / "score_model_away.pkl"),
            'feature_scaler': joblib.load(models_path / "feature_scaler.pkl"),
            'feature_columns': joblib.load(models_path / "feature_columns.pkl")
        }


def main():
    """
    Main execution: Train ML models on historical NFL data.
    """
    print("=" * 60)
    print("NFL ML MODEL TRAINING")
    print("=" * 60)

    # Load data
    data_file = "data/nfl_plays_2023.csv"
    if not Path(data_file).exists():
        print(f"❌ Error: {data_file} not found")
        print("Run 'python data/fetch_nfl_data.py' first to download data")
        sys.exit(1)

    print(f"\n📂 Loading data from {data_file}...")
    df = pd.read_csv(data_file)
    print(f"✓ Loaded {len(df):,} plays from {len(df['game_id'].unique())} games")

    # Initialize trainer
    trainer = NFLModelTrainer(models_dir="models")

    # Engineer features
    df = trainer.engineer_features(df)

    # Prepare training data
    X, y_win, y_home_score, y_away_score = trainer.prepare_training_data(df)

    # Train models
    trainer.train_win_probability_model(X, y_win)
    trainer.train_score_prediction_models(X, y_home_score, y_away_score)

    # Save models
    trainer.save_models()

    print("\n" + "=" * 60)
    print("✓ MODEL TRAINING COMPLETE")
    print("=" * 60)
    print("\nModels ready for streaming inference!")
    print("\nNext steps:")
    print("1. Start Kafka: docker-compose up -d")
    print("2. Start consumer: python consumer/spark_consumer.py")
    print("3. Start producer: python producer/kafka_producer.py")


if __name__ == "__main__":
    main()
