# NFL Streaming Pipeline - Makefile
# ==================================
# Convenient commands for common tasks

.PHONY: help setup install kafka-start kafka-stop kafka-status fetch-data train consumer producer run clean test

help: ## Show this help message
	@echo "NFL Streaming Pipeline - Available Commands"
	@echo "============================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup (venv, dependencies, Kafka)
	@./scripts/setup.sh

install: ## Install Python dependencies
	pip install -r requirements.txt

kafka-start: ## Start Kafka infrastructure
	docker-compose up -d
	@echo "⏳ Waiting for Kafka to be ready..."
	@sleep 10
	@echo "✓ Kafka is ready at localhost:9093"
	@echo "📊 Kafka UI: http://localhost:8080"

kafka-stop: ## Stop Kafka infrastructure
	docker-compose down

kafka-status: ## Check Kafka status
	docker-compose ps

fetch-data: ## Download NFL play-by-play data
	python data/fetch_nfl_data.py

train: ## Train ML models
	python models/train_models.py

consumer: ## Run Spark consumer (in foreground)
	python consumer/spark_consumer.py

producer: ## Run Kafka producer (Super Bowl LVII)
	python producer/kafka_producer.py --game-file data/game_super_bowl_57.csv

run: ## Run full pipeline (data + train + stream)
	@./scripts/run_pipeline.sh

clean: ## Clean generated files
	@./scripts/cleanup.sh

test: ## Run tests (if implemented)
	pytest tests/ -v

lint: ## Run code quality checks
	flake8 data/ models/ producer/ consumer/ --max-line-length=100
	black --check data/ models/ producer/ consumer/

format: ## Auto-format code
	black data/ models/ producer/ consumer/
