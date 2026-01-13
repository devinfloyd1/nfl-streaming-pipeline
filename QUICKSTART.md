# Quick Start Guide

Get the NFL streaming pipeline running in 5 minutes.

## Prerequisites

- Python 3.9+
- Docker Desktop (running)
- 4GB RAM available

## Option 1: Automated Setup (Recommended)

```bash
# Clone and navigate to project
cd nfl-streaming-pipeline

# Run automated setup
./scripts/setup.sh

# Activate virtual environment
source venv/bin/activate

# Fetch data
python data/fetch_nfl_data.py

# Train models
python models/train_models.py

# Terminal 1: Start consumer
python consumer/spark_consumer.py

# Terminal 2: Start producer
python producer/kafka_producer.py
```

## Option 2: Using Makefile

```bash
# Initial setup
make setup

# Fetch data and train models
make fetch-data
make train

# Run pipeline (in separate terminals)
make consumer    # Terminal 1
make producer    # Terminal 2
```

## Option 3: Manual Step-by-Step

### 1. Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Kafka

```bash
docker-compose up -d

# Wait 10 seconds for Kafka to start
sleep 10
```

### 3. Download NFL Data

```bash
python data/fetch_nfl_data.py
```

**Expected output:**
```
📊 Fetching NFL play-by-play data for seasons: [2023]
✓ Downloaded 40,000+ plays from 200+ games
✓ Filtered from 50,000+ to 40,000+ plays
💾 Saved to data/nfl_plays_2023.csv
```

### 4. Train ML Models

```bash
python models/train_models.py
```

**Expected output:**
```
🎯 Training Win Probability Model (Logistic Regression)...
✓ Model trained on 30,000+ plays
  Accuracy: 0.850
  ROC-AUC: 0.905

📈 Training Final Score Prediction Models (Linear Regression)...
✓ Home Score Model: MAE: 7.2 points, R²: 0.78
✓ Away Score Model: MAE: 7.5 points, R²: 0.75
```

### 5. Start Consumer (Terminal 1)

```bash
python consumer/spark_consumer.py
```

**Wait for:**
```
📦 Loading ML models...
✓ Models loaded successfully
📡 Connecting to Kafka topic 'nfl-plays'...
✓ Kafka stream created

🏈 LIVE GAME PREDICTIONS - Streaming Started
```

### 6. Start Producer (Terminal 2)

Open a **new terminal**, activate venv, and run:

```bash
source venv/bin/activate
python producer/kafka_producer.py --game-file data/game_super_bowl_57.csv
```

**You should see predictions streaming in Terminal 1:**
```
Play #  1 | Q1 15:00 | KC  0 -  0 PHI | PHI 52.3% win prob | Projected: KC 24 - 27 PHI
Play #  5 | Q1 13:21 | KC  0 -  0 PHI | PHI 54.1% win prob | Projected: KC 23 - 28 PHI
...
```

## Verification

### Check Kafka is Running

```bash
docker-compose ps
```

Should show:
- nfl-zookeeper (Up)
- nfl-kafka (Up)
- nfl-kafka-ui (Up)

### Check Data Files

```bash
ls -lh data/
```

Should show:
- nfl_plays_2023.csv (~50MB)
- nfl_games_2023.csv (~50KB)
- game_super_bowl_57.csv (~500KB)

### Check Models

```bash
ls -lh models/
```

Should show:
- win_probability_model.pkl
- score_model_home.pkl
- score_model_away.pkl
- feature_scaler.pkl
- feature_columns.pkl

### Check Predictions

```bash
ls -lh predictions/
```

Should show CSV files with timestamps:
- predictions_20240113_143022_batch_0.csv
- predictions_20240113_143023_batch_1.csv
- ...

## Common Issues

### Issue: "No Kafka brokers available"

**Solution:**
```bash
docker-compose down
docker-compose up -d
sleep 10
```

### Issue: "Models not found"

**Solution:**
```bash
python models/train_models.py
```

### Issue: "Data file not found"

**Solution:**
```bash
python data/fetch_nfl_data.py
```

### Issue: Docker not running

**Solution:**
Start Docker Desktop application, then:
```bash
docker-compose up -d
```

### Issue: Port already in use

**Solution:**
```bash
# Check what's using port 9093
lsof -i :9093

# Stop Kafka and restart
docker-compose down
docker-compose up -d
```

## Next Steps

1. **Explore predictions:** Check CSV files in `predictions/` directory
2. **Try different games:** Use other CSV files from `data/`
3. **Adjust parameters:** Edit `.env` file
4. **View Kafka UI:** Visit http://localhost:8080
5. **Read docs:** See [README.md](README.md) for full documentation

## Stopping the Pipeline

1. **Stop producer:** Ctrl+C in Terminal 2
2. **Stop consumer:** Ctrl+C in Terminal 1
3. **Stop Kafka:**
   ```bash
   docker-compose down
   ```

## Clean Up

To remove all generated files:

```bash
./scripts/cleanup.sh

# Or manually:
rm -rf data/*.csv
rm -rf models/*.pkl
rm -rf predictions/
docker-compose down -v
```

## Getting Help

- **Documentation:** [README.md](README.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues:** Check troubleshooting section in README

## Customization

### Stream a different game

```bash
# List available games
cat data/nfl_games_2023.csv

# Stream specific game
python producer/kafka_producer.py --game-file data/game_YYYY_WW_AWAY_HOME.csv
```

### Change streaming speed

```bash
# Faster (0.1s delay)
python producer/kafka_producer.py --delay 0.1

# Slower (2s delay)
python producer/kafka_producer.py --delay 2.0
```

### Limit number of plays

```bash
# Stream only first 50 plays
python producer/kafka_producer.py --max-plays 50
```

## Success Criteria

You should see:
- ✅ Kafka running (3 containers)
- ✅ Data downloaded (40,000+ plays)
- ✅ Models trained (5 .pkl files)
- ✅ Consumer streaming predictions
- ✅ Producer sending plays
- ✅ CSV files in predictions/

**Congratulations!** Your NFL streaming pipeline is running. 🏈

For detailed explanation of concepts, see [ARCHITECTURE.md](ARCHITECTURE.md).
