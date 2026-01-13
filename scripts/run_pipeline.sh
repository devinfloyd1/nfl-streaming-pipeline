#!/bin/bash

# NFL Streaming Pipeline - Run Script
# ====================================
# Runs the complete pipeline in sequence

set -e

echo "======================================================================"
echo "NFL STREAMING PIPELINE - FULL RUN"
echo "======================================================================"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found. Run scripts/setup.sh first."
    exit 1
fi

# Check if Kafka is running
echo ""
echo "🔍 Checking Kafka status..."
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Kafka not running. Starting Kafka..."
    docker-compose up -d
    sleep 10
fi
echo "✓ Kafka is running"

# Fetch data if needed
echo ""
echo "📊 Checking for NFL data..."
if [ ! -f "data/nfl_plays_2023.csv" ]; then
    echo "📥 Fetching NFL data..."
    python data/fetch_nfl_data.py
else
    echo "✓ Data already exists"
fi

# Train models if needed
echo ""
echo "🤖 Checking for trained models..."
if [ ! -f "models/win_probability_model.pkl" ]; then
    echo "🎯 Training ML models..."
    python models/train_models.py
else
    echo "✓ Models already trained"
fi

# Run consumer in background
echo ""
echo "🚀 Starting Spark consumer..."
python consumer/spark_consumer.py &
CONSUMER_PID=$!
sleep 5

# Run producer
echo ""
echo "🚀 Starting Kafka producer..."
python producer/kafka_producer.py --game-file data/game_super_bowl_57.csv

# Wait a bit for final predictions
sleep 3

# Stop consumer
echo ""
echo "⏹️  Stopping consumer..."
kill $CONSUMER_PID 2>/dev/null || true

echo ""
echo "======================================================================"
echo "✓ PIPELINE RUN COMPLETE"
echo "======================================================================"
echo ""
echo "📁 Check predictions/ directory for output CSV files"
echo ""
