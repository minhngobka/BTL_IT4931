# Technical Documentation

Comprehensive technical details about the Big Data Customer Journey Analytics system.

---

## 📐 System Architecture

### Overview

The project implements a **Kappa Architecture** - a simplified alternative to Lambda architecture that uses a single real-time processing pipeline.

```
┌─────────────────┐
│  2019-Oct.csv   │
│   (5.3GB data)  │
└────────┬────────┘
         │
    ┌────▼─────────────┐
    │   simulator.py   │  Python Kafka Producer
    │  (Event Stream)  │  Sends JSON events
    └────────┬─────────┘
             │
    ┌────────▼──────────┐
    │   Apache Kafka    │  Message Queue
    │  (3 partitions)   │  Topic: customer_events
    │   Strimzi 0.35    │  NodePort: 31927
    └────────┬──────────┘
             │
  ┌──────────▼───────────────┐
  │  Spark Structured        │
  │  Streaming 3.5.0         │
  ├──────────────────────────┤
  │ • Stream-Static Join     │  Product Catalog Broadcast
  │ • Windowed Aggregations  │  Tumbling (5min), Sliding (10min)
  │ • Stateful Analytics     │  Session Tracking
  │ • Custom UDFs            │  Feature Engineering
  │ • Watermarking (10min)   │  Late Data Handling
  └──────────┬───────────────┘
             │
      ┌──────▼────────┐
      │   MongoDB     │  NoSQL Database
      │   Bitnami     │  9 Collections
      └───────────────┘
             │
  ┌──────────▼───────────────┐
  │  Spark Batch ML          │  Scheduled (6 hours)
  │  (K-Means, Random Forest)│  Or Manual Trigger
  └──────────────────────────┘
```

### Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **Apache Spark** | 3.5.0 | Distributed stream & batch processing |
| **Apache Kafka (Strimzi)** | 0.35 | Message queue with 3 partitions |
| **MongoDB (Bitnami)** | Latest | NoSQL analytics database |
| **Kubernetes (Minikube)** | v1.25+ | Container orchestration |
| **Docker** | 20.10+ | Containerization |
| **Python** | 3.10+ | Application language |

### Why Kappa Architecture?

**vs Lambda Architecture:**

| Aspect | Lambda | Kappa (This Project) |
|--------|--------|----------------------|
| **Pipelines** | 2 (batch + speed) | 1 (stream only) |
| **Complexity** | High | Lower |
| **Code Duplication** | Separate batch & stream logic | Single codebase |
| **Latency** | Mixed (batch = hours) | Consistent (seconds) |
| **Maintenance** | Two systems to maintain | One system |
| **Best For** | Mixed workloads | Real-time priority |

---

## 🎯 Data Flow

### 1. Data Ingestion

**simulator.py** → **Kafka**

```python
# Reads 2019-Oct.csv in chunks (1000 records/batch)
# Sends JSON events to Kafka topic "customer_events"
# Throttled: 0.01s sleep between events

Event Schema:
{
  "event_time": "2019-10-01 00:00:00 UTC",
  "event_type": "view",  // or "cart", "purchase"
  "product_id": 3900821,
  "category_id": 2053013552326770905,
  "brand": "aqua",
  "price": 33.20,
  "user_id": 554748717,
  "user_session": "9333dfbd-b87a-4708-9857-6336556b0fcc"
}
```

### 2. Stream Processing

**Kafka** → **Spark Streaming** → **MongoDB**

**Pipeline Stages:**

```python
# Stage 1: Read from Kafka
df_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "my-cluster-kafka-bootstrap:9092") \
    .option("subscribe", "customer_events") \
    .option("startingOffsets", "latest") \
    .option("maxOffsetsPerTrigger", "10000") \
    .load()

# Stage 2: Parse JSON
df_parsed = df_kafka.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# Stage 3: Enrich (Broadcast Join)
df_enriched = df_parsed.join(
    broadcast(product_catalog_df),  # Static table (CSV)
    "product_id",
    "left"
)

# Stage 4: Feature Engineering (Custom UDFs)
df_features = df_enriched \
    .withColumn("price_category", classify_price_udf(col("price"))) \
    .withColumn("event_hour", hour(col("event_timestamp"))) \
    .withColumn("is_weekend", is_weekend_udf(col("event_timestamp")))

# Stage 5: Watermarking (Handle Late Data)
df_watermarked = df_features.withWatermark("event_timestamp", "10 minutes")

# Stage 6: Complex Aggregations
# - Tumbling window (5 min)
# - Sliding window (10 min, slide 5 min)
# - Session-based (stateful)

# Stage 7: Write to MongoDB (Exactly-Once)
query = df_aggregated.writeStream \
    .format("mongodb") \
    .option("checkpointLocation", "/checkpoints") \
    .option("idempotent", "true") \
    .start()
```

### 3. Batch ML Processing

**MongoDB** → **Spark Batch** → **MongoDB**

Triggered manually or scheduled (every 6 hours):

```python
# Read enriched events from MongoDB
df = spark.read.format("mongodb") \
    .option("collection", "enriched_events") \
    .load()

# Feature Engineering (40+ features)
features = feature_engineering(df)

# K-Means Clustering
kmeans = KMeans(k=4, featuresCol="features")
model = kmeans.fit(features)
segments = model.transform(features)

# Random Forest Classification
rf = RandomForestClassifier(featuresCol="features", labelCol="churn")
rf_model = rf.fit(train_data)
predictions = rf_model.transform(test_data)

# Write results back to MongoDB
segments.write.format("mongodb") \
    .option("collection", "customer_segments") \
    .save()
```

---

## ✨ Advanced Spark Features

### 1. Complex Aggregations

**Tumbling Windows (5 minutes):**
```python
df_window_agg = df_enriched \
    .groupBy(
        window(col("event_timestamp"), "5 minutes"),
        col("category_name"),
        col("event_type")
    ) \
    .agg(
        count("*").alias("event_count"),
        approx_count_distinct("user_id").alias("unique_users"),
        avg("price").alias("avg_price"),
        sum("price").alias("total_revenue"),
        stddev("price").alias("price_stddev")
    )
```

**Sliding Windows (10 min window, 5 min slide):**
```python
df_sliding_agg = df_enriched \
    .groupBy(
        window(col("event_timestamp"), "10 minutes", "5 minutes"),
        col("brand")
    ) \
    .agg(
        count("*").alias("event_count"),
        approx_count_distinct("user_id").alias("unique_users"),
        avg("price").alias("avg_price")
    )
```

### 2. Stream-Static Joins (Broadcast)

```python
# Load product catalog (static table)
product_catalog_df = spark.read.csv("product_catalog.csv", header=True)

# Broadcast to all executors (efficient for small tables)
df_enriched = df_stream.join(
    broadcast(product_catalog_df),
    "product_id",
    "left"
)
```

**Why Broadcast?**
- Avoids shuffle (network I/O)
- Replicates small table to each executor
- O(1) lookup vs O(n) shuffle join

### 3. Custom UDFs (User-Defined Functions)

```python
@udf(returnType=StringType())
def classify_price_category(price):
    """Categorize prices into tiers"""
    if price is None:
        return "Unknown"
    elif price < 50:
        return "Budget"
    elif price < 200:
        return "Mid-Range"
    else:
        return "Premium"

# Register and use
classify_price_udf = classify_price_category
df = df.withColumn("price_category", classify_price_udf(col("price")))
```

### 4. Stateful Session Analytics

```python
df_session_agg = df_enriched \
    .groupBy("user_session", "user_id") \
    .agg(
        count("*").alias("total_events"),
        approx_count_distinct("product_id").alias("unique_products_viewed"),
        sum(when(col("event_type") == "view", 1).otherwise(0)).alias("view_count"),
        sum(when(col("event_type") == "cart", 1).otherwise(0)).alias("cart_count"),
        sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("purchase_count"),
        sum(when(col("event_type") == "purchase", col("price")).otherwise(0)).alias("total_purchase_value"),
        collect_set("category_name").alias("categories_browsed"),
        min("event_timestamp").alias("session_start"),
        max("event_timestamp").alias("session_end")
    ) \
    .withColumn("session_duration_minutes", 
        (unix_timestamp("session_end") - unix_timestamp("session_start")) / 60
    ) \
    .withColumn("conversion_rate", 
        when(col("total_events") > 0, col("purchase_count") / col("total_events")).otherwise(0)
    )
```

### 5. Watermarking (Late Data Handling)

```python
# Define watermark: allow events up to 10 minutes late
df_watermarked = df_enriched.withWatermark("event_timestamp", "10 minutes")

# Events older than (max_event_time - 10 minutes) are dropped
# Prevents unbounded state growth
```

**How It Works:**
```
Current Max Event Time: 10:15:00
Watermark: 10:05:00 (10 min behind)

Events with timestamp < 10:05:00 → Dropped (too late)
Events with timestamp >= 10:05:00 → Processed
```

### 6. Exactly-Once Semantics

```python
query = df_aggregated.writeStream \
    .format("mongodb") \
    .option("checkpointLocation", "/opt/spark/work-dir/checkpoints") \
    .outputMode("append") \
    .option("idempotent", "true") \  # Write each batch only once
    .start()
```

**Guarantees:**
- **Checkpointing**: State saved after each batch
- **Idempotent Writes**: Same batch won't be written twice
- **Fault Tolerance**: Recovers from failures without duplicates

---

## 🤖 Machine Learning Pipeline

### Feature Engineering (40+ Features)

```python
def feature_engineering(df):
    return df \
        .withColumn("hour_of_day", hour("event_timestamp")) \
        .withColumn("day_of_week", dayofweek("event_timestamp")) \
        .withColumn("is_weekend", dayofweek("event_timestamp").isin([1, 7])) \
        .withColumn("session_duration_hours", 
            (unix_timestamp("session_end") - unix_timestamp("session_start")) / 3600
        ) \
        .withColumn("avg_time_between_events",
            col("session_duration_hours") / col("total_events")
        ) \
        .withColumn("purchase_rate", col("purchase_count") / col("total_events")) \
        .withColumn("cart_abandonment_rate",
            when(col("cart_count") > 0, 
                1 - (col("purchase_count") / col("cart_count"))
            ).otherwise(0)
        ) \
        # ... 30+ more features
```

### K-Means Clustering

**Purpose:** Customer segmentation into 4 groups

```python
# Prepare features
assembler = VectorAssembler(
    inputCols=feature_columns,
    outputCol="features"
)
feature_vector = assembler.transform(df)

# Scale features (important for distance-based algorithms)
scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
scaler_model = scaler.fit(feature_vector)
scaled_data = scaler_model.transform(feature_vector)

# Train K-Means
kmeans = KMeans(k=4, featuresCol="scaled_features", predictionCol="cluster")
model = kmeans.fit(scaled_data)

# Assign clusters
segments = model.transform(scaled_data)
```

**Typical Segments:**
- **Cluster 0:** Browsers (high views, low purchases)
- **Cluster 1:** Converters (balanced funnel)
- **Cluster 2:** Bargain Hunters (low prices, high purchases)
- **Cluster 3:** Premium Buyers (high prices, fewer items)

### Random Forest Classification

**Purpose:** Predict customer churn

```python
# Define churn (no activity in recent period)
df_with_churn = df.withColumn("churn",
    when(datediff(current_date(), col("last_event_date")) > 30, 1).otherwise(0)
)

# Train-test split
train, test = df_with_churn.randomSplit([0.8, 0.2], seed=42)

# Train Random Forest
rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="churn",
    numTrees=100,
    maxDepth=10,
    featureSubsetStrategy="auto"
)
rf_model = rf.fit(train)

# Predict
predictions = rf_model.transform(test)

# Evaluate
evaluator = BinaryClassificationEvaluator(labelCol="churn", metricName="areaUnderROC")
auc = evaluator.evaluate(predictions)  # Typical: 0.75-0.85
```

**Feature Importance:**
- Session duration
- Purchase frequency
- Days since last activity
- Average order value
- Cart abandonment rate

### Time Series Analysis

```python
# Hourly patterns
hourly_stats = df.groupBy("hour_of_day") \
    .agg(
        count("*").alias("event_count"),
        countDistinct("user_id").alias("unique_users"),
        avg("price").alias("avg_price")
    ) \
    .orderBy("hour_of_day")

# Daily patterns
daily_stats = df.groupBy("day_of_week") \
    .agg(
        count("*").alias("event_count"),
        sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("purchases")
    ) \
    .orderBy("day_of_week")
```

---

## 📊 MongoDB Collections Schema

### 1. enriched_events

**Purpose:** Raw events with product metadata

```javascript
{
  _id: ObjectId("..."),
  event_timestamp: ISODate("2019-10-01T00:00:00.000Z"),
  event_type: "view",  // view, cart, purchase
  product_id: 3900821,
  product_name: "aqua Appliances Model 717",
  category_name: "aqua",
  brand: "aqua",
  price: 33.2,
  price_category: "Budget",  // Budget, Mid-Range, Premium
  user_id: 554748717,
  user_session: "9333dfbd-...",
  event_hour: 0,
  is_weekend: false,
  processing_timestamp: ISODate("2025-11-25T10:04:30.018Z"),
  _epoch_id: 1  // For idempotency
}
```

### 2. user_session_analytics

**Purpose:** Aggregated user behavior per session

```javascript
{
  _id: ObjectId("..."),
  user_session: "0ac92940-...",
  user_id: 552783882,
  total_events: 13,
  unique_products_viewed: 12,
  view_count: 13,
  cart_count: 0,
  purchase_count: 0,
  total_purchase_value: 0.0,
  avg_product_price: 251.75,
  categories_browsed: ["samsung", "Generic"],
  brands_viewed: ["samsung", "NaN"],
  session_start: ISODate("2019-10-01T00:01:30.000Z"),
  session_end: ISODate("2019-10-01T00:13:07.000Z"),
  session_duration_minutes: 11.62,
  has_view: true,
  has_cart: false,
  has_purchase: false,
  conversion_rate: 0.0,
  _epoch_id: 1
}
```

### 3. conversion_funnel

**Purpose:** Time-windowed conversion metrics

```javascript
{
  _id: ObjectId("..."),
  time_window: {
    start: ISODate("2019-10-01T01:30:00.000Z"),
    end: ISODate("2019-10-01T01:45:00.000Z")  // 15-min windows
  },
  total_sessions: 29,
  sessions_with_view: 29,
  sessions_with_cart: 0,
  sessions_with_purchase: 0,
  avg_session_duration: 0.94,  // minutes
  avg_purchase_value: 0.0,
  view_to_cart_rate: 0.0,       // % sessions that add to cart
  cart_to_purchase_rate: 0.0,   // % carts that convert
  overall_conversion_rate: 0.0, // % sessions that purchase
  _epoch_id: 1
}
```

### 4. event_aggregations

**Purpose:** Windowed statistics (5-min tumbling, 10-min sliding)

```javascript
{
  _id: ObjectId("..."),
  time_window: {
    start: ISODate("2019-10-01T00:00:00.000Z"),
    end: ISODate("2019-10-01T00:05:00.000Z")
  },
  category_name: "electronics",
  event_type: "view",
  event_count: 156,
  unique_users: 142,
  unique_sessions: 138,
  avg_price: 125.45,
  total_revenue: 19570.20,
  max_price: 599.99,
  min_price: 12.50,
  price_stddev: 87.32,
  _epoch_id: 3
}
```

### 5. customer_segments (Batch ML)

**Purpose:** K-Means cluster assignments

```javascript
{
  _id: ObjectId("..."),
  user_id: 554748717,
  cluster: 2,  // 0-3
  cluster_name: "Bargain Hunters",
  features: {
    avg_price: 45.20,
    purchase_frequency: 0.15,
    session_duration_avg: 8.5,
    cart_abandonment_rate: 0.05
    // ... more features
  },
  distance_to_center: 2.34
}
```

### 6. churn_predictions (Batch ML)

**Purpose:** Random Forest churn probability

```javascript
{
  _id: ObjectId("..."),
  user_id: 552783882,
  churn_probability: 0.73,  // 0.0-1.0
  churn_prediction: 1,      // 0 (active) or 1 (churn)
  risk_level: "High",       // Low, Medium, High
  last_activity_days: 45,
  total_purchases: 3,
  avg_order_value: 125.50,
  feature_importance: {
    "days_since_last_activity": 0.35,
    "purchase_frequency": 0.22,
    "avg_session_duration": 0.18
    // ... more features
  }
}
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# Kafka Configuration
KAFKA_EXTERNAL_BROKER=192.168.49.2:31927  # Minikube IP:NodePort
KAFKA_TOPIC=customer_events

# MongoDB Configuration
MONGODB_HOST=localhost  # When port-forwarding
MONGODB_PORT=27017
MONGODB_DATABASE=bigdata_db

# Simulator Settings
CSV_FILE_PATH=2019-Oct.csv
CHUNK_SIZE=1000  # Records per batch
SLEEP_TIME=0.01  # Seconds between events

# Minikube
MINIKUBE_IP=192.168.49.2
```

### Kubernetes Resources

**Spark Streaming Deployment:**
```yaml
resources:
  requests:
    memory: "3Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

**Spark Batch Job:**
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "6Gi"
    cpu: "3000m"
```

**MongoDB:**
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
```

### Spark Configuration

```python
spark = SparkSession.builder \
    .appName("AdvancedCustomerJourneyStreaming") \
    .config("spark.mongodb.write.connection.uri", mongodb_uri) \
    .config("spark.sql.streaming.checkpointLocation", checkpoint_path) \
    .config("spark.sql.shuffle.partitions", "8") \
    .config("spark.sql.adaptive.enabled", "false")  # Disabled for streaming
    .config("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false") \
    .getOrCreate()
```

---

## 📈 Performance Metrics

### Expected Throughput

| Component | Metric | Value |
|-----------|--------|-------|
| **Kafka** | Events/sec | ~1,000 |
| **Spark Streaming** | Micro-batch interval | 5-10 seconds |
| **Spark Streaming** | Records/batch | 5,000-10,000 |
| **MongoDB** | Writes/sec | ~2,000 |
| **End-to-end Latency** | Ingestion to storage | <30 seconds |

### Resource Usage (Minikube)

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| **Spark Streaming** | 1-2 cores | 3-4 GB | ~1 GB (checkpoints) |
| **Spark Batch** | 2-3 cores | 4-6 GB | Temporary |
| **Kafka** | 0.5 core | 1 GB | ~500 MB (logs) |
| **MongoDB** | 0.5 core | 1 GB | ~2 GB (data) |
| **Total** | 4 cores | 8 GB | ~5 GB |

---

## 🎯 Academic Features Checklist

| Category | Feature | Implementation |
|----------|---------|----------------|
| **Aggregations** | Complex windowed | ✅ Tumbling (5min), Sliding (10min/5min) |
| **Joins** | Stream-static | ✅ Broadcast join with product catalog |
| **Custom Functions** | UDFs | ✅ Price categorization, time features |
| **State Management** | Stateful operations | ✅ Session-based aggregations |
| **Windows** | Multiple types | ✅ Time-based, session-based |
| **Machine Learning** | Clustering & Classification | ✅ K-Means (4 clusters), Random Forest |
| **Fault Tolerance** | Exactly-once semantics | ✅ Checkpointing + idempotent writes |

---

## 🔍 Monitoring & Observability

### Spark UI Metrics

**Access:** http://localhost:4040 (via port-forward)

**Key Tabs:**
- **Jobs:** DAG visualization, stages, tasks
- **Stages:** Task distribution, shuffle metrics
- **Storage:** Cached tables, memory usage
- **Streaming:** Batch processing times, input rates
- **SQL:** Query plans, statistics

### Kubernetes Monitoring

```bash
# Pod status
kubectl get pods

# Resource usage
kubectl top pods

# Logs
kubectl logs -f deployment/spark-streaming-advanced

# Events
kubectl get events --sort-by='.lastTimestamp'
```

### MongoDB Metrics

```javascript
// Connection stats
db.serverStatus().connections

// Collection stats
db.enriched_events.stats()

// Query performance
db.enriched_events.find({event_type: "purchase"}).explain("executionStats")
```

---

**For setup instructions:** See [SETUP_GUIDE.md](SETUP_GUIDE.md)  
**For quick reference:** See [README.md](README.md)
