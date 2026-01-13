# Architecture Deep Dive

## System Design

### Overview

The NFL Streaming Pipeline is designed to demonstrate production-quality streaming data architecture patterns commonly used in real-time analytics and ML serving.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                     │
└─────────────────────────────────────────────────────────────────────┘

Historical Data → Feature Engineering → Model Training → Model Artifacts
                                                                ↓
         Kafka Producer ← Play-by-Play Data ← CSV Files       Models
                ↓                                               ↓
         Kafka Topic (nfl-plays)                          Load Models
                ↓                                               ↓
         Spark Streaming Consumer ────────────────────────────→ Inference
                ↓
         Predictions (Console + CSV)
```

## Components

### 1. Data Layer

**Technology:** nfl-data-py + pandas

**Responsibilities:**
- Fetch play-by-play data from nflfastR
- Clean and filter to relevant plays
- Export game files for streaming

**Design Decisions:**
- Use nflfastR for data quality (used by NFL teams)
- CSV storage for simplicity (could use Parquet for production)
- Game-level files enable selective streaming

**Code:** [`data/fetch_nfl_data.py`](data/fetch_nfl_data.py)

### 2. ML Training Layer

**Technology:** scikit-learn + joblib

**Responsibilities:**
- Feature engineering from raw play data
- Train supervised learning models
- Serialize models for inference

**Feature Engineering:**

```python
# Time-based features
- time_remaining_pct: Normalized time (0-1)
- is_fourth_quarter: Binary indicator
- quarter: Current quarter (1-4)

# Score-based features
- score_differential: Home - Away
- current_home_score: Absolute score
- current_away_score: Absolute score
- is_close_game: Within 7 points
- is_blowout: More than 21 points

# Field position features
- field_position_pct: Yards to goal (0-1)
- down: Current down (1-4)
- distance: Yards to first down
- down_distance_ratio: Difficulty metric

# Context features
- is_home_team: Home field advantage
- is_first_half / is_second_half: Game phase
```

**Model Selection:**

| Model | Purpose | Why This Choice |
|-------|---------|-----------------|
| Logistic Regression | Win Probability | Fast inference, probabilistic output, interpretable |
| Linear Regression | Score Prediction | Simple, fast, sufficient accuracy for demo |

**Alternative Considerations:**

For production, could use:
- **XGBoost/LightGBM**: Better accuracy, still fast
- **Neural Networks**: Capture non-linear patterns
- **Ensemble Methods**: Combine multiple models

Trade-off: Accuracy vs. Latency vs. Complexity

**Code:** [`models/train_models.py`](models/train_models.py)

### 3. Message Queue Layer

**Technology:** Apache Kafka

**Responsibilities:**
- Reliable message delivery
- Ordered play-by-play stream
- Decouple producer and consumer

**Kafka Configuration:**

```yaml
Partitions: 1 (ensures ordering)
Replication: 1 (single broker setup)
Retention: 24 hours
Compression: gzip (reduce bandwidth)
```

**Topic Design:**

```
Topic: nfl-plays
Key: game_id (ensures same game → same partition)
Value: JSON play data
```

**Why Kafka?**

Alternatives considered:
- **RabbitMQ**: Good, but less common in data engineering
- **AWS Kinesis**: Cloud-only, vendor lock-in
- **Pub/Sub**: Cloud-only, vendor lock-in
- **Redis Streams**: Less durable, lighter weight

Kafka chosen for:
- Industry standard for data streaming
- Excellent durability and scalability
- Strong ecosystem (Spark, Flink, etc.)
- Portfolio relevance (used at most tech companies)

### 4. Stream Processing Layer

**Technology:** PySpark Structured Streaming

**Responsibilities:**
- Consume messages from Kafka
- Apply ML models in real-time
- Output predictions

**Architecture Pattern:**

```python
# Micro-batch processing
Stream → Batch → Transform → Predict → Output
         (100ms)

# Each micro-batch:
1. Read N messages from Kafka
2. Parse JSON to DataFrame
3. Engineer features
4. Scale features (StandardScaler)
5. Predict (loaded models)
6. Display + Save results
```

**Why PySpark?**

Alternatives considered:
- **Plain kafka-python**: Simpler but no fault tolerance
- **Kafka Streams**: Java-based
- **Apache Flink**: More complex, similar capabilities

PySpark chosen for:
- Scalability (1 node → 1000 nodes, same code)
- Fault tolerance (automatic checkpointing)
- Integration (native Kafka connector)
- Python ecosystem (pandas, sklearn)

**Code:** [`consumer/spark_consumer.py`](consumer/spark_consumer.py)

### 5. Streaming Producer

**Technology:** kafka-python

**Responsibilities:**
- Read game data from CSV
- Stream plays sequentially to Kafka
- Simulate real-time pace

**Design Pattern:**

```python
for each play in game:
    message = create_json(play)
    producer.send(topic, message)
    sleep(0.5s)  # Simulate real-time
```

**Rate Control:**

Configurable delay between plays:
- 0.5s default (realistic pace)
- Can speed up for testing
- Can slow down for demo

**Code:** [`producer/kafka_producer.py`](producer/kafka_producer.py)

## Data Flow

### 1. Training Phase (Offline)

```
CSV Data → Feature Engineering → Train Models → Save .pkl files
  (GB)         (pandas)           (sklearn)         (joblib)

Time: ~2 minutes for full season
```

### 2. Streaming Phase (Online)

```
CSV → Producer → Kafka → Consumer → ML Models → Predictions
(1)      (2)      (3)       (4)         (5)          (6)

(1) Read play-by-play CSV
(2) Send JSON messages (0.5s delay)
(3) Topic: nfl-plays (persistent log)
(4) Spark reads micro-batches
(5) Load models, predict
(6) Display + save results
```

**Latency Breakdown:**

| Stage | Latency | Notes |
|-------|---------|-------|
| Producer → Kafka | ~5ms | Network + serialize |
| Kafka storage | ~1ms | Disk write |
| Kafka → Consumer | ~5ms | Network + deserialize |
| Feature engineering | ~1ms | Pandas operations |
| ML inference | ~2ms | sklearn prediction |
| **Total** | **~15ms** | Well under 100ms SLA |

## Scalability

### Current Setup (Local)

- Single Kafka broker
- Single Spark executor
- Processes ~2 plays/second

### Production Scaling

**Horizontal Scaling:**

```
Kafka Cluster:
- 3+ brokers (HA)
- Multiple partitions (parallel processing)
- Replication factor 3 (fault tolerance)

Spark Cluster:
- Multiple executors
- Process 1000s plays/second
- Automatic load balancing
```

**Vertical Scaling:**

- More memory for larger models
- More CPU for parallel inference
- GPU for deep learning models

### Cloud Deployment

**AWS Architecture:**

```
┌─────────────────────────────────────────────────────┐
│                    AWS Cloud                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  S3 ← Play Data                                     │
│   ↓                                                  │
│  Lambda → MSK (Managed Kafka) → EMR (Spark)        │
│                                      ↓               │
│                               CloudWatch ← Metrics   │
│                                      ↓               │
│                               S3 ← Predictions       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Cost Estimate:**
- MSK: ~$100/month (small cluster)
- EMR: ~$200/month (2 nodes)
- S3: ~$5/month (storage)
- Total: ~$300/month

## Fault Tolerance

### Kafka Guarantees

- **Durability**: Messages replicated to disk
- **Ordering**: Within-partition ordering guaranteed
- **Replay**: Can re-read old messages

### Spark Checkpointing

```python
query = df.writeStream \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .start()
```

On failure:
1. Spark reads checkpoint
2. Determines last processed offset
3. Resumes from that point
4. No duplicate processing

## Monitoring

### Metrics to Track (Production)

**Kafka:**
- Messages/second
- Consumer lag
- Disk usage
- Network throughput

**Spark:**
- Processing time per batch
- Records processed/second
- Memory usage
- Failed tasks

**ML Models:**
- Prediction latency (p50, p95, p99)
- Model accuracy over time
- Feature distribution drift

**Tools:**
- Prometheus (metrics collection)
- Grafana (dashboards)
- PagerDuty (alerting)

## Security Considerations

### Current Setup (Development)

- No authentication
- No encryption
- Local network only

### Production Hardening

```
┌─────────────────────────────────────────┐
│        Security Layers                   │
├─────────────────────────────────────────┤
│ 1. Network: VPC, Security Groups        │
│ 2. Auth: SASL/SCRAM (Kafka)            │
│ 3. Encryption: TLS in-transit           │
│ 4. Encryption: At-rest (S3, EBS)       │
│ 5. IAM: Least-privilege roles           │
│ 6. Secrets: AWS Secrets Manager         │
└─────────────────────────────────────────┘
```

## Testing Strategy

### Unit Tests

```python
# Test feature engineering
def test_feature_engineering():
    play_data = {...}
    features = engineer_features(play_data)
    assert features['time_remaining_pct'] == 0.5

# Test predictions
def test_win_probability():
    features = {...}
    prob = model.predict_proba(features)
    assert 0 <= prob <= 1
```

### Integration Tests

- End-to-end pipeline test
- Producer → Kafka → Consumer
- Verify predictions written to CSV

### Load Tests

- Stream 1000 plays/second
- Monitor latency and throughput
- Identify bottlenecks

## Future Enhancements

### 1. Real-Time Data Source

Replace CSV with live API:
```python
# ESPN API (unofficial)
# TheOddsAPI (betting odds)
# NFL GamePass API
```

### 2. Advanced ML

- **LSTM/Transformer**: Sequence modeling
- **Reinforcement Learning**: Play calling strategy
- **Multi-task Learning**: Predict multiple outcomes

### 3. Feature Store

```
Feast / Tecton:
- Centralized feature management
- Online/offline consistency
- Feature versioning
```

### 4. Model Registry

```
MLflow / SageMaker:
- Version control for models
- A/B testing framework
- Canary deployments
```

## Learning Resources

### Kafka
- [Kafka: The Definitive Guide](https://www.confluent.io/resources/kafka-the-definitive-guide/)
- [Designing Data-Intensive Applications](https://dataintensive.net/)

### PySpark
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [Spark: The Definitive Guide](https://www.oreilly.com/library/view/spark-the-definitive/9781491912201/)

### ML in Production
- [Designing Machine Learning Systems](https://www.oreilly.com/library/view/designing-machine-learning/9781098107956/)
- [Machine Learning Design Patterns](https://www.oreilly.com/library/view/machine-learning-design/9781098115777/)

## Questions?

This architecture document explains the technical decisions and trade-offs in this project. For implementation details, see the code comments in each module.
