# Project Structure

## Directory Tree

```
nfl-streaming-pipeline/
│
├── 📁 data/                          # Data fetching and storage
│   ├── __init__.py
│   ├── fetch_nfl_data.py            # Download NFL data from nflfastR
│   ├── nfl_plays_2023.csv           # Full season data (generated)
│   ├── nfl_games_2023.csv           # Game list (generated)
│   └── game_super_bowl_57.csv       # Sample game (generated)
│
├── 📁 models/                        # ML training and model storage
│   ├── __init__.py
│   ├── train_models.py              # Train ML models
│   ├── win_probability_model.pkl    # Logistic regression (generated)
│   ├── score_model_home.pkl         # Linear regression home (generated)
│   ├── score_model_away.pkl         # Linear regression away (generated)
│   ├── feature_scaler.pkl           # StandardScaler (generated)
│   └── feature_columns.pkl          # Feature list (generated)
│
├── 📁 producer/                      # Kafka producer
│   ├── __init__.py
│   └── kafka_producer.py            # Stream plays to Kafka
│
├── 📁 consumer/                      # PySpark consumer
│   ├── __init__.py
│   └── spark_consumer.py            # Consume & predict
│
├── 📁 config/                        # Configuration
│   ├── __init__.py
│   └── settings.py                  # Centralized config
│
├── 📁 scripts/                       # Automation scripts
│   ├── setup.sh                     # Initial setup
│   ├── run_pipeline.sh              # Run full pipeline
│   └── cleanup.sh                   # Clean generated files
│
├── 📁 predictions/                   # Prediction outputs (generated)
│   └── predictions_*.csv            # Timestamped predictions
│
├── 📄 docker-compose.yml            # Kafka infrastructure
├── 📄 requirements.txt              # Python dependencies
├── 📄 Makefile                      # Convenience commands
├── 📄 .env                          # Environment variables
├── 📄 .env.example                  # Environment template
├── 📄 .gitignore                    # Git ignore rules
│
├── 📄 README.md                     # Main documentation
├── 📄 QUICKSTART.md                 # 5-minute getting started
├── 📄 ARCHITECTURE.md               # Technical deep dive
├── 📄 PROJECT_SUMMARY.md            # Portfolio summary
├── 📄 CONTRIBUTING.md               # Contribution guidelines
└── 📄 LICENSE                       # MIT License
```

## File Purposes

### Core Application Files

| File | Lines | Purpose |
|------|-------|---------|
| `data/fetch_nfl_data.py` | ~250 | Download & clean NFL data |
| `models/train_models.py` | ~400 | Feature engineering & ML training |
| `producer/kafka_producer.py` | ~300 | Stream plays to Kafka |
| `consumer/spark_consumer.py` | ~400 | PySpark consumer with ML inference |

### Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Kafka cluster setup (Zookeeper, Broker, UI) |
| `requirements.txt` | Python package dependencies |
| `.env` | Runtime configuration variables |
| `config/settings.py` | Centralized configuration loader |

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Complete project documentation (setup, usage, architecture) |
| `QUICKSTART.md` | Fast-track guide to get running in 5 minutes |
| `ARCHITECTURE.md` | Deep technical explanation of design decisions |
| `PROJECT_SUMMARY.md` | Portfolio presentation & talking points |
| `CONTRIBUTING.md` | Guidelines for contributors |

### Automation Scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup.sh` | Automated initial setup (venv, Kafka, dependencies) |
| `scripts/run_pipeline.sh` | Run complete pipeline end-to-end |
| `scripts/cleanup.sh` | Stop services & clean generated files |
| `Makefile` | Convenience commands (make setup, make run, etc.) |

## Data Flow Through Files

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                │
└─────────────────────────────────────────────────────────────────┘

1. TRAINING PHASE (Offline)
   ─────────────────────────
   fetch_nfl_data.py
         │
         ├─→ Downloads from nflfastR
         ├─→ Cleans & filters
         └─→ Saves: data/nfl_plays_2023.csv
                │
                ↓
   train_models.py
         │
         ├─→ Loads CSV
         ├─→ Engineers features
         ├─→ Trains models
         └─→ Saves: models/*.pkl
                │
                ↓
   [Models ready for inference]

2. STREAMING PHASE (Online)
   ─────────────────────────
   kafka_producer.py
         │
         ├─→ Reads: data/game_*.csv
         ├─→ Converts to JSON
         └─→ Sends to Kafka topic
                │
                ↓
   [Kafka broker stores messages]
                │
                ↓
   spark_consumer.py
         │
         ├─→ Consumes from Kafka
         ├─→ Loads: models/*.pkl
         ├─→ Engineers features
         ├─→ Predicts
         ├─→ Displays to console
         └─→ Saves: predictions/*.csv
                │
                ↓
   [Predictions available for analysis]
```

## Module Dependencies

```
┌───────────────────────────────────────────────────────────┐
│                    DEPENDENCIES                            │
└───────────────────────────────────────────────────────────┘

data/fetch_nfl_data.py
  ├── nfl_data_py (external)
  └── pandas

models/train_models.py
  ├── pandas
  ├── numpy
  ├── sklearn
  └── joblib

producer/kafka_producer.py
  ├── kafka-python
  ├── pandas
  └── config/settings.py

consumer/spark_consumer.py
  ├── pyspark
  ├── pandas
  ├── joblib
  └── config/settings.py

config/settings.py
  ├── python-dotenv
  └── .env file
```

## Generated Files (Not in Git)

These files are created during setup and operation:

```
📁 data/
   ├── nfl_plays_2023.csv          (~50 MB)
   ├── nfl_games_2023.csv          (~50 KB)
   └── game_super_bowl_57.csv      (~500 KB)

📁 models/
   ├── win_probability_model.pkl   (~2 MB)
   ├── score_model_home.pkl        (~2 MB)
   ├── score_model_away.pkl        (~2 MB)
   ├── feature_scaler.pkl          (~10 KB)
   └── feature_columns.pkl         (~1 KB)

📁 predictions/
   └── predictions_*_batch_*.csv   (~100 KB each)

📁 venv/                            (virtual environment)
   └── ...                          (~500 MB)
```

## Docker Volumes

```
docker-compose.yml creates:

📦 kafka-data                       (Kafka logs & messages)
   └── ...                          (~100 MB)
```

## Configuration Flow

```
1. .env.example
      ↓ (copy)
   .env
      ↓ (loaded by)
   config/settings.py
      ↓ (imported by)
   producer/kafka_producer.py
   consumer/spark_consumer.py
```

## Execution Order

### First-Time Setup
```
1. scripts/setup.sh
   ├─→ Creates venv
   ├─→ Installs requirements.txt
   ├─→ Copies .env.example → .env
   └─→ Starts docker-compose.yml

2. data/fetch_nfl_data.py
   └─→ Downloads & processes data

3. models/train_models.py
   └─→ Trains & saves models
```

### Running the Pipeline
```
Terminal 1:
  consumer/spark_consumer.py
     ↓
  [Waits for Kafka messages]

Terminal 2:
  producer/kafka_producer.py
     ↓
  [Streams plays to Kafka]
     ↓
  [Consumer receives & predicts]
```

## Size Breakdown

| Component | Size | Notes |
|-----------|------|-------|
| Source code | ~2 KB | Python files |
| Documentation | ~50 KB | Markdown files |
| Dependencies (venv) | ~500 MB | Python packages |
| Data files | ~50 MB | CSV files |
| Model files | ~10 MB | Serialized models |
| Docker volumes | ~100 MB | Kafka data |
| **Total** | **~650 MB** | Full project |

## Port Usage

| Port | Service | Purpose |
|------|---------|---------|
| 2181 | Zookeeper | Kafka coordination |
| 9092 | Kafka (internal) | Internal broker |
| 9093 | Kafka (external) | External connections |
| 8080 | Kafka UI | Web interface |

## Environment Variables

Referenced in `.env`:

| Variable | Default | Used By |
|----------|---------|---------|
| KAFKA_BOOTSTRAP_SERVERS | localhost:9093 | Producer, Consumer |
| KAFKA_TOPIC | nfl-plays | Producer, Consumer |
| NFL_SEASON | 2023 | Data fetcher |
| PLAY_DELAY_SECONDS | 0.5 | Producer |
| MAX_PLAYS_PER_GAME | 200 | Producer |
| SPARK_APP_NAME | NFL-ML-Predictions | Consumer |
| SPARK_LOG_LEVEL | WARN | Consumer |

## Quick Reference

### Start Services
```bash
make kafka-start        # Start Kafka
make fetch-data         # Download data
make train              # Train models
make consumer           # Run consumer (Terminal 1)
make producer           # Run producer (Terminal 2)
```

### Stop Services
```bash
Ctrl+C                  # Stop consumer/producer
make kafka-stop         # Stop Kafka
make clean              # Clean all generated files
```

### Check Status
```bash
make kafka-status       # Check Kafka containers
ls data/                # Check data files
ls models/              # Check model files
ls predictions/         # Check prediction outputs
```

## Code Statistics

```
Language: Python
Files: 8 (.py files)
Lines: ~1,500 (excluding comments)
Documentation: ~800 lines (markdown)
Comments: ~300 lines (inline)
```

## Testing Structure (Future)

```
tests/                              # To be implemented
├── unit/
│   ├── test_feature_engineering.py
│   ├── test_model_training.py
│   └── test_predictions.py
├── integration/
│   ├── test_pipeline.py
│   └── test_kafka_flow.py
└── conftest.py                     # pytest fixtures
```

---

This structure is designed for:
- **Clarity:** Easy to navigate
- **Modularity:** Independent components
- **Scalability:** Add features without refactoring
- **Production-readiness:** Proper separation of concerns
- **Portfolio value:** Clear organization for reviewers
