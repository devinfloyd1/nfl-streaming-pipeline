#!/bin/bash

# NFL Streaming Pipeline - Setup Script
# =====================================
# Automates the initial setup process

set -e  # Exit on error

echo "======================================================================"
echo "NFL STREAMING PIPELINE - SETUP"
echo "======================================================================"

# Check Python version
echo ""
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.9+ required (found $python_version)"
    exit 1
fi
echo "✓ Python $python_version"

# Check Docker
echo ""
echo "🐳 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found. Please install Docker Desktop."
    exit 1
fi
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon not running. Please start Docker Desktop."
    exit 1
fi
echo "✓ Docker is running"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file
echo ""
echo "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file (you can customize this later)"
else
    echo "✓ .env file already exists"
fi

# Start Kafka
echo ""
echo "🚀 Starting Kafka infrastructure..."
docker-compose up -d

echo ""
echo "⏳ Waiting for Kafka to be ready..."
sleep 10

# Check if Kafka is running
if docker-compose ps | grep -q "Up"; then
    echo "✓ Kafka is running"
else
    echo "❌ Error: Kafka failed to start"
    docker-compose logs
    exit 1
fi

echo ""
echo "======================================================================"
echo "✓ SETUP COMPLETE"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Fetch NFL data:"
echo "   python data/fetch_nfl_data.py"
echo ""
echo "3. Train ML models:"
echo "   python models/train_models.py"
echo ""
echo "4. Run the pipeline:"
echo "   Terminal 1: python consumer/spark_consumer.py"
echo "   Terminal 2: python producer/kafka_producer.py"
echo ""
echo "📚 See README.md for detailed instructions"
echo ""
