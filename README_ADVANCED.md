# 🚀 Advanced Big Data Project: E-Commerce Customer Journey Analytics

## 📋 Project Overview

This project implements a **Kappa Architecture** for real-time customer journey analysis in an e-commerce environment. The system processes behavioral data (views, cart additions, purchases) using Apache Spark, Kafka, and MongoDB, deployed on Kubernetes.

### ✨ Key Features

- **Real-time Stream Processing**: Complex event processing with Spark Structured Streaming
- **Advanced Machine Learning**: Customer segmentation, churn prediction, and behavioral analysis
- **Scalable Architecture**: Kubernetes deployment with auto-scaling capabilities
- **Comprehensive Analytics**: Window aggregations, funnel analysis, and time series forecasting
- **Production-Ready**: Exactly-once processing, fault tolerance, and monitoring

---

## 🏗️ Architecture

### Kappa Architecture Implementation

```
┌─────────────┐      ┌──────────┐      ┌─────────────────┐      ┌──────────┐
│   Event     │─────▶│  Apache  │─────▶│  Spark Stream   │─────▶│ MongoDB  │
│  Simulator  │      │  Kafka   │      │   Processing    │      │ (Sink)   │
└─────────────┘      └──────────┘      └─────────────────┘      └──────────┘
                                               │
                                               │ Checkpoints
                                               ▼
                                        ┌─────────────────┐
                                        │  Kubernetes     │
                                        │  Persistent     │
                                        │  Volume         │
                                        └─────────────────┘
                                        
                                        ┌─────────────────┐
                                        │  Spark Batch    │
                                        │  ML Analytics   │◀────── MongoDB
                                        └─────────────────┘
```

### Why Kappa vs Lambda?

**Our Choice: Kappa Architecture**

**Advantages:**
- ✅ Simpler codebase - single processing pipeline
- ✅ Lower maintenance overhead
- ✅ Real-time results with eventual consistency
- ✅ Easier to debug and test
- ✅ Cost-effective for our use case

**Lambda Architecture Comparison:**
- Lambda requires separate batch and speed layers
- More complex to maintain two codebases
- Better for cases requiring perfect historical accuracy
- Higher operational complexity

**Our Justification:**
For e-commerce analytics, real-time insights with eventual consistency are sufficient. The Kappa architecture allows us to reprocess historical data through the same stream processing pipeline if needed, maintaining code simplicity while meeting business requirements.

---

## 🎯 Spark Features Demonstrated

### 1. Complex Aggregations ✅

**Window Functions:**
```python
# Tumbling windows: 5-minute windows
window(col("event_timestamp"), "5 minutes")

# Sliding windows: 10-minute windows, sliding every 5 minutes
window(col("event_timestamp"), "10 minutes", "5 minutes")

# Session windows with watermarking
df.withWatermark("event_timestamp", "10 minutes")
```

**Advanced Aggregation Functions:**
- `count()`, `sum()`, `avg()`, `min()`, `max()`
- `countDistinct()`, `approx_count_distinct()`
- `stddev()`, `variance()`, `corr()`
- `collect_list()`, `collect_set()`
- `first()`, `last()`
- `percentile_approx()`

### 2. Pivot/Unpivot Operations ✅

```python
# Pivot: Convert event types to columns
df_pivot = df.groupBy("hour_window", "category") \
    .pivot("event_type", ["view", "cart", "purchase"]) \
    .agg(count("*"), sum("price"))
```

### 3. Custom UDFs ✅

**Scalar UDF:**
```python
@udf(returnType=StringType())
def classify_price_category(price):
    if price < 20: return "Budget"
    elif price < 100: return "Mid-Range"
    else: return "Premium"
```

**Pandas UDF (Vectorized):**
```python
@pandas_udf(DoubleType())
def calculate_session_quality(event_counts, purchases, avg_price):
    return (event_counts * 0.3 + purchases * 0.5 + avg_price * 0.2) * 100
```

### 4. Join Operations ✅

**Broadcast Join (Stream-Static):**
```python
df_enriched = df_stream.join(
    broadcast(df_products),  # Small dimension table
    "product_id",
    "left_outer"
)
```

**Sort-Merge Join:**
```python
df_result = df_large1.join(
    df_large2,
    df_large1.id == df_large2.id,
    "inner"
)
```

### 5. Performance Optimization ✅

**Caching and Persistence:**
```python
df_user_features.cache()  # In-memory caching
df_events.persist(StorageLevel.MEMORY_AND_DISK)
```

**Partition Pruning:**
```python
df.filter(col("event_timestamp").between(start_date, end_date))
```

**Bucketing:**
```python
df.write.bucketBy(10, "user_id").sortBy("event_timestamp").saveAsTable("events")
```

**Adaptive Query Execution:**
```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
```

### 6. Streaming Processing ✅

**Structured Streaming:**
- Multiple output modes: append, update, complete
- Watermarking for late data handling
- State management for aggregations
- Exactly-once processing guarantees
- Multiple concurrent queries

**State Management:**
```python
df.groupBy("user_session") \
    .agg(...)  # Maintains state across micro-batches
```

### 7. Machine Learning (Spark MLlib) ✅

**Customer Segmentation (K-Means):**
```python
kmeans = KMeans(k=4, seed=42)
pipeline = Pipeline(stages=[assembler, scaler, kmeans])
model = pipeline.fit(df_features)
```

**Churn Prediction (Random Forest):**
```python
rf = RandomForestClassifier(
    labelCol="is_churned",
    numTrees=100,
    maxDepth=10
)
model = rf.fit(train_data)
```

**Feature Engineering:**
- VectorAssembler for feature preparation
- StandardScaler for normalization
- PCA for dimensionality reduction
- StringIndexer and OneHotEncoder

### 8. Time Series Analysis ✅

```python
# Moving averages
window_7day = Window.partitionBy("event_type") \
    .orderBy("date") \
    .rowsBetween(-6, 0)

df.withColumn("ma_7day", avg("event_count").over(window_7day))

# Day-over-day growth
df.withColumn("prev_day", lag("event_count", 1).over(window_prev_day))
```

### 9. Statistical Computations ✅

- Descriptive statistics: mean, median, std, percentiles
- Correlation analysis
- Chi-square tests
- Skewness and kurtosis

---

## 📦 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Stream Processing** | Apache Spark 3.5.0 (Structured Streaming) | Real-time data processing |
| **Message Queue** | Apache Kafka (Strimzi Operator) | Event ingestion and buffering |
| **NoSQL Database** | MongoDB | Data persistence and querying |
| **Container Orchestration** | Kubernetes (Minikube) | Deployment and scaling |
| **ML Framework** | Spark MLlib | Machine learning models |
| **Language** | Python 3.10+ (PySpark) | Application development |
| **Build Tool** | Docker | Container image creation |

---

## 🛠️ Installation and Setup

### Prerequisites

1. **Hardware Requirements:**
   - CPU: 4+ cores
   - RAM: 8GB+ (16GB recommended)
   - Disk: 20GB+ free space

2. **Software Requirements:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install -y git docker.io python3.10 python3-pip
   
   # Install Minikube
   curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
   sudo install minikube-linux-amd64 /usr/local/bin/minikube
   
   # Install kubectl
   sudo snap install kubectl --classic
   
   # Install Helm
   sudo snap install helm --classic
   ```

### Project Setup

#### Step 1: Clone Repository

```bash
git clone https://github.com/minhngobka/BTL_IT4931.git
cd bigdata_project
```

#### Step 2: Download Dataset

Download the e-commerce dataset from Kaggle:
- **URL:** https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store
- **File:** `2019-Oct.csv`
- Place the file in the project root directory

#### Step 3: Generate Dimension Tables

```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate dimension tables
python generate_dimensions.py
```

This creates:
- `user_dimension.csv` - User demographics and segments
- `product_catalog.csv` - Enhanced product information
- `category_hierarchy.csv` - Category taxonomy

#### Step 4: Start Kubernetes Cluster

```bash
# Start Minikube with sufficient resources
minikube start --driver=docker --cpus=4 --memory=8g

# Verify cluster is running
kubectl get nodes
```

#### Step 5: Deploy Infrastructure

```bash
# Add Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add strimzi https://strimzi.io/charts/
helm repo update

# Install MongoDB
helm install my-mongo bitnami/mongodb --set auth.enabled=false

# Install Strimzi Kafka Operator
helm install strimzi-operator strimzi/strimzi-kafka-operator

# Wait for operators to be ready
kubectl get pods -w
# Wait until all pods are "Running"

# Deploy Kafka cluster
kubectl apply -f kafka-combined.yaml

# Wait for Kafka to be ready
kubectl get pods -w
# Wait for my-cluster-kafka-0 to be "Running"
```

#### Step 6: Build Docker Image

```bash
# Build Spark application image
eval $(minikube docker-env)  # Use Minikube's Docker daemon
docker build -t bigdata-spark:latest .

# Verify image
docker images | grep bigdata-spark
```

#### Step 7: Deploy Spark Applications

```bash
# Deploy streaming and batch applications
kubectl apply -f k8s-spark-apps.yaml

# Check deployment status
kubectl get deployments
kubectl get pods

# View logs
kubectl logs -f deployment/spark-streaming-advanced
```

---

## 🚀 Running the System

### 1. Start Data Simulator

```bash
# Terminal 1: Port forward Kafka (for external access)
kubectl port-forward service/my-cluster-kafka-external-bootstrap 9094:9094

# Terminal 2: Get Kafka connection info
KAFKA_IP=$(minikube ip)
KAFKA_PORT=$(kubectl get service my-cluster-kafka-external-bootstrap -o=jsonpath='{.spec.ports[0].nodePort}')
echo "Kafka: $KAFKA_IP:$KAFKA_PORT"

# Update simulator.py with the Kafka address
# Edit line: KAFKA_BROKER = '<KAFKA_IP>:<KAFKA_PORT>'

# Run simulator
python simulator.py
```

### 2. Monitor Streaming Application

```bash
# View streaming logs
kubectl logs -f deployment/spark-streaming-advanced

# Access Spark UI (port-forward)
kubectl port-forward deployment/spark-streaming-advanced 4040:4040
# Open browser: http://localhost:4040
```

### 3. Run Batch ML Analytics

```bash
# Manual execution
kubectl create job spark-batch-manual --from=cronjob/spark-batch-ml-scheduled

# Check job status
kubectl get jobs
kubectl logs job/spark-batch-manual

# Scheduled execution runs every 6 hours automatically
```

### 4. Query Results from MongoDB

```bash
# Port-forward MongoDB
kubectl port-forward service/my-mongo-mongodb 27017:27017

# Connect with MongoDB client
mongosh mongodb://localhost:27017

# Query collections
use bigdata_db

# View enriched events
db.enriched_events.find().limit(5)

# View aggregations
db.event_aggregations.find().sort({_id: -1}).limit(10)

# View customer segments
db.customer_segments.find()

# View churn predictions
db.churn_predictions.find({churn_prediction: 1}).limit(10)

# View conversion funnel
db.conversion_funnel.find().sort({_id: -1}).limit(5)
```

---

## 📊 Analytics Outputs

### Collections in MongoDB

| Collection | Description | Update Frequency |
|------------|-------------|------------------|
| `enriched_events` | Raw events with dimension data | Real-time (streaming) |
| `event_aggregations` | Window-based aggregations | Every 30 seconds |
| `user_session_analytics` | Session-level metrics | Every 30 seconds |
| `conversion_funnel` | Funnel conversion rates | Every 15 minutes |
| `user_feature_engineering` | ML features for each user | Batch (6 hours) |
| `customer_segments` | K-Means clustering results | Batch (6 hours) |
| `churn_predictions` | Churn probability per user | Batch (6 hours) |
| `time_series_analysis` | Daily trends and patterns | Batch (6 hours) |
| `statistical_analysis` | Statistical summaries | Batch (6 hours) |

---

## 🔧 Configuration

### Spark Configuration

Edit `k8s-spark-apps.yaml` to adjust Spark settings:

```yaml
# Memory allocation
--driver-memory 2g
--executor-memory 2g

# Parallelism
spark.sql.shuffle.partitions: "8"
spark.default.parallelism: "8"

# Adaptive execution
spark.sql.adaptive.enabled: "true"
```

### Kafka Configuration

Edit `kafka-combined.yaml`:

```yaml
spec:
  kafka:
    replicas: 1  # Increase for production
    listeners:
      - name: plain
        port: 9092
        type: internal
```

### MongoDB Configuration

```bash
# For production, enable authentication
helm install my-mongo bitnami/mongodb \
  --set auth.enabled=true \
  --set auth.rootPassword=<your-password>
```

---

## 🧪 Testing and Validation

### Unit Tests

```bash
# Run PySpark tests
python -m pytest tests/

# Test individual components
python -m pytest tests/test_streaming.py
python -m pytest tests/test_ml_models.py
```

### Integration Tests

```bash
# Test end-to-end pipeline
kubectl apply -f tests/test-pipeline.yaml

# Validate data quality
python validate_results.py
```

---

## 📈 Performance Tuning

### Spark Optimization Tips

1. **Partition Count:**
   ```python
   # Rule of thumb: 2-3 partitions per CPU core
   spark.conf.set("spark.sql.shuffle.partitions", "16")
   ```

2. **Memory Management:**
   ```python
   # Increase driver memory for large collections
   --driver-memory 4g
   
   # Adjust memory fraction
   spark.conf.set("spark.memory.fraction", "0.8")
   ```

3. **Broadcast Threshold:**
   ```python
   # Increase for larger dimension tables
   spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "20971520")  # 20MB
   ```

### Kubernetes Scaling

```bash
# Scale streaming deployment
kubectl scale deployment spark-streaming-advanced --replicas=2

# Increase resource limits
kubectl edit deployment spark-streaming-advanced
# Adjust resources.limits.memory and resources.limits.cpu
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Kafka Connection Timeout**
```bash
# Verify Kafka service
kubectl get service | grep kafka

# Check Kafka logs
kubectl logs my-cluster-kafka-0

# Test connectivity
kubectl run -it --rm --restart=Never kafka-test --image=bitnami/kafka:latest -- \
  kafka-console-consumer.sh --bootstrap-server my-cluster-kafka-bootstrap:9092 --topic customer_events
```

**2. MongoDB Connection Refused**
```bash
# Check MongoDB status
kubectl get pods | grep mongo

# View MongoDB logs
kubectl logs my-mongo-mongodb-0

# Verify service
kubectl get service my-mongo-mongodb
```

**3. Spark Application Crashes**
```bash
# Check resource limits
kubectl describe pod <spark-pod-name>

# View detailed logs
kubectl logs <spark-pod-name> --previous

# Increase memory
kubectl edit deployment spark-streaming-advanced
```

**4. Checkpoint Directory Issues**
```bash
# Clear checkpoints (development only)
kubectl exec -it <spark-pod> -- rm -rf /opt/spark/work-dir/checkpoints/*

# Use PersistentVolume for production
kubectl apply -f k8s-spark-apps.yaml  # Includes PVC configuration
```

---

## 📚 Project Structure

```
bigdata_project/
├── streaming_app_advanced.py       # Advanced streaming with all Spark features
├── batch_analytics_ml.py           # ML-based batch analytics
├── streaming_app.py                # Original simple streaming app
├── streaming_app_k8s.py            # K8s-optimized streaming app
├── journey_analysis.py             # Original journey analysis
├── simulator.py                    # Event data simulator
├── generate_dimensions.py          # Dimension table generator
├── Dockerfile                      # Spark application image
├── kafka-combined.yaml             # Kafka cluster configuration
├── k8s-spark-apps.yaml             # Kubernetes deployments
├── requirements.txt                # Python dependencies
├── README_ADVANCED.md              # This file
├── product_catalog.csv             # Product dimension
├── user_dimension.csv              # User dimension (generated)
├── category_hierarchy.csv          # Category dimension (generated)
└── 2019-Oct.csv                    # Event data (from Kaggle)
```

---

## 🎓 Learning Outcomes

This project demonstrates:

1. ✅ **Kappa Architecture** implementation
2. ✅ **Apache Spark** intermediate-level skills
3. ✅ **Kubernetes** deployment and orchestration
4. ✅ **Real-time streaming** with exactly-once semantics
5. ✅ **Machine Learning** with Spark MLlib
6. ✅ **Performance optimization** techniques
7. ✅ **Data engineering** best practices
8. ✅ **Production-ready** big data system

---

## 🤝 Contributors

- **Team**: Big Data Storage and Processing Course
- **Dataset**: Kaggle - E-commerce Behavior Data
- **Technologies**: Apache Spark, Kafka, MongoDB, Kubernetes

---

## 📄 License

This project is for educational purposes as part of the Big Data Storage and Processing course.

---

## 🔗 References

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Spark MLlib Guide](https://spark.apache.org/docs/latest/ml-guide.html)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Strimzi Kafka Operator](https://strimzi.io/)
- [Kappa Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/)

---

## 🆘 Support

For questions or issues:
1. Check the troubleshooting section
2. Review Spark application logs
3. Consult the course materials
4. Contact the teaching team

---

**Happy Big Data Processing! 🚀**
