#!/bin/bash

# NFL Streaming Pipeline - Cleanup Script
# ========================================
# Cleans up generated files and stops services

echo "======================================================================"
echo "NFL STREAMING PIPELINE - CLEANUP"
echo "======================================================================"

# Stop Kafka
echo ""
echo "🛑 Stopping Kafka..."
docker-compose down
echo "✓ Kafka stopped"

# Optional: Remove generated data (commented out for safety)
echo ""
echo "🧹 Cleanup options:"
echo ""
echo "To remove generated files, run:"
echo "  rm -rf data/*.csv           # Remove downloaded data"
echo "  rm -rf models/*.pkl         # Remove trained models"
echo "  rm -rf predictions/*.csv    # Remove prediction outputs"
echo ""
echo "To remove Docker volumes:"
echo "  docker-compose down -v"
echo ""
echo "To remove virtual environment:"
echo "  rm -rf venv/"
echo ""

echo "======================================================================"
echo "✓ CLEANUP COMPLETE"
echo "======================================================================"
