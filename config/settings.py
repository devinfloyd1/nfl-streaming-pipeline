"""
Configuration Settings
======================
Centralized configuration for the NFL streaming pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9093")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "nfl-plays")

# Data Configuration
NFL_SEASON = int(os.getenv("NFL_SEASON", "2023"))
DATA_DIR = PROJECT_ROOT / os.getenv("DATA_DIR", "data")
MODELS_DIR = PROJECT_ROOT / os.getenv("MODELS_DIR", "models")
PREDICTIONS_DIR = PROJECT_ROOT / os.getenv("PREDICTIONS_DIR", "predictions")

# Producer Configuration
PLAY_DELAY_SECONDS = float(os.getenv("PLAY_DELAY_SECONDS", "0.5"))
MAX_PLAYS_PER_GAME = int(os.getenv("MAX_PLAYS_PER_GAME", "200"))

# Consumer Configuration
SPARK_APP_NAME = os.getenv("SPARK_APP_NAME", "NFL-ML-Predictions")
SPARK_LOG_LEVEL = os.getenv("SPARK_LOG_LEVEL", "WARN")

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
PREDICTIONS_DIR.mkdir(exist_ok=True)
