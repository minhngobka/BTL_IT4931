# Big Data Customer Journey Analytics

Real-time e-commerce customer journey analytics system using Apache Spark, Kafka, and MongoDB.

## 📖 About This Project

This project demonstrates a **real-time big data analytics pipeline** for analyzing customer behavior in an e-commerce platform. It processes millions of events (views, carts, purchases) in real-time to generate insights about customer journeys, conversion funnels, and behavior patterns.

**Key Features:**
- ⚡ **Real-time streaming** with Apache Spark Structured Streaming
- 📊 **Complex aggregations** (windowed, stateful, sessionization)
- 🔗 **Stream-static joins** with product catalogs
- 🤖 **Machine Learning** (K-Means clustering, Random Forest classification)
- 🎯 **Exactly-once semantics** with checkpointing
- 📈 **Analytics dashboard** via MongoDB queries

## 🏗️ Architecture

```
CSV Data (5.3GB) → Kafka → Spark Streaming → MongoDB
                              ↓
                      Batch ML Jobs (6 hours)
```

**Technology Stack:**
- **Apache Spark 3.5.0** - Stream & batch processing
- **Apache Kafka (Strimzi)** - Message queue (3 partitions)
- **MongoDB (Bitnami)** - Analytics database (9 collections)
- **Kubernetes (Minikube)** - Container orchestration
- **Python 3.10+** - Application language
- **Docker** - Containerization

## 🚀 Quick Start (5 Steps)

```bash
# 1. Clone the repository
git clone https://github.com/minhngobka/BTL_IT4931.git
cd BTL_IT4931

# 2. Download dataset (5.3GB)
# Get 2019-Oct.csv from: https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store
# Place it in: data/raw/ecommerce_events_2019_oct.csv

# 3. Start Minikube with sufficient resources
minikube start --cpus=4 --memory=8192

# 4. Run automated deployment (installs Kafka, MongoDB, Spark)
./scripts/deploy_all.sh

# 5. Update Kafka broker address and start simulator
export MINIKUBE_IP=$(minikube ip)
sed -i "s|KAFKA_EXTERNAL_BROKER=.*|KAFKA_EXTERNAL_BROKER=$MINIKUBE_IP:31927|" config/.env
python src/utils/event_simulator.py
```

**⏱️ Total time:** ~25 minutes

## 📋 Prerequisites

Before running the project, ensure you have:

**Required Software:**
- **Docker** (20.10+) 
- **Minikube** (v1.25+)
- **kubectl** (v1.25+)
- **Helm** (v3.0+)
- **Python 3.10+**

**System Requirements:**
- **CPU:** 4 cores minimum
- **RAM:** 8GB minimum
- **Disk:** 20GB free space
- **OS:** Linux (Ubuntu 20.04+)

**Quick Install Commands:**
```bash
# Docker
sudo apt install docker.io
sudo usermod -aG docker $USER

# Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# kubectl
sudo snap install kubectl --classic

# Helm
sudo snap install helm --classic

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📁 Project Structure

```
bigdata_project/
├── src/                          # Source code
│   ├── streaming/                # Real-time streaming apps
│   │   ├── streaming_basic.py
│   │   ├── streaming_advanced.py    # ← Main production app
│   │   └── streaming_kubernetes.py
│   ├── batch/                    # Batch processing
│   │   ├── ml_analytics.py          # ← ML pipeline
│   │   └── journey_analysis.py
│   └── utils/                    # Utilities
│       ├── event_simulator.py       # ← Kafka producer
│       ├── dimension_generator.py
│       └── validate_environment.sh
├── data/
│   ├── raw/                      # Raw data (CSV)
│   └── catalog/                  # Dimension tables
├── config/                       # Configuration files
│   ├── .env                      # Local environment
│   ├── .env.example              # Template
│   └── kafka-strimzi.yaml
├── kubernetes/                   # K8s manifests
│   └── spark-deployments.yaml
├── scripts/
│   └── deploy_all.sh             # ← Run this!
├── docs/                         # Documentation
│   ├── README.md
│   ├── SETUP_GUIDE.md
│   └── TECHNICAL_DOCS.md
└── Dockerfile
```

## 🎯 What It Does

### Real-Time Analytics

**Input:** E-commerce events (view, cart, purchase)
```json
{
  "event_time": "2019-10-01 00:00:00 UTC",
  "event_type": "purchase",
  "product_id": 3900821,
  "brand": "samsung",
  "price": 489.99,
  "user_id": 554748717,
  "user_session": "9333dfbd-b87a-4708-9857-6336556b0fcc"
}
```

**Processing:**
- Enriches events with product metadata (broadcast join)
- Calculates windowed aggregations (5-min tumbling, 10-min sliding)
- Tracks user sessions with state management
- Analyzes conversion funnels (view → cart → purchase)

**Output:** 9 MongoDB collections with insights
- `enriched_events` - Processed events
- `user_session_analytics` - Session-level metrics
- `conversion_funnel` - Conversion rates
- `event_aggregations` - Time-windowed stats
- `customer_segments` - ML clustering results
- `churn_predictions` - Churn probability scores

### Batch Machine Learning

**K-Means Clustering (4 clusters):**
- Segments customers based on behavior patterns
- Features: purchase frequency, avg order value, session duration

**Random Forest Classification:**
- Predicts customer churn
- 80/20 train-test split
- AUC: 0.75-0.85

## 🔧 Configuration

Edit `config/.env` for your environment:

```env
# Kafka
KAFKA_EXTERNAL_BROKER=192.168.49.2:31927  # Update with minikube ip
KAFKA_TOPIC=customer_events

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=bigdata_db

# Simulator
CSV_FILE_PATH=data/raw/ecommerce_events_2019_oct.csv
CHUNK_SIZE=1000
SLEEP_TIME=0.01
```

## 📊 Monitoring & Verification

### Check Deployment Status

```bash
# Check all pods are running
kubectl get pods

# Expected output:
# my-cluster-kafka-0                Running
# my-cluster-zookeeper-0            Running
# my-mongo-mongodb-0                Running
# spark-streaming-advanced-xxx      Running
```

### Monitor Spark Streaming

```bash
# Port-forward Spark UI
kubectl port-forward deployment/spark-streaming-advanced 4040:4040

# Open in browser: http://localhost:4040
```

### Query MongoDB

```bash
# ⭐ CÁCH TỐT NHẤT: Query trực tiếp vào pod MongoDB (đáng tin cậy 100%)
bash scripts/demo_mongodb.sh

# HOẶC query thủ công:
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  print('📊 Total records:', db.enriched_events.countDocuments());
  db.enriched_events.find().limit(2).forEach(printjson);
"

# Query với aggregation pipeline
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  db.enriched_events.aggregate([
    {\$match: {event_type: 'view'}},
    {\$group: {_id: '\$product_id', views: {\$sum: 1}}},
    {\$sort: {views: -1}},
    {\$limit: 5}
  ]).forEach(printjson)
"

# 💡 LƯU Ý: Port-forward tới localhost có thể không ổn định
# Khuyến nghị dùng kubectl exec để query trực tiếp vào pod
```

### Check Kafka

```bash
# List topics
kubectl exec -it my-cluster-kafka-0 -- bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# Consume messages
kubectl exec -it my-cluster-kafka-0 -- bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic customer_events --from-beginning --max-messages 10
```

## 🐛 Troubleshooting

### Pods Stuck in Pending/ImagePullBackOff

```bash
# Check pod details
kubectl describe pod <pod-name>

# Reload Docker image to Minikube
docker build -t bigdata-spark:latest .
minikube image load bigdata-spark:latest

# Restart deployment
kubectl rollout restart deployment/spark-streaming-advanced
```

### Kafka Connection Failed

```bash
# Get Minikube IP
minikube ip

# Update .env file
sed -i "s|KAFKA_EXTERNAL_BROKER=.*|KAFKA_EXTERNAL_BROKER=$(minikube ip):31927|" config/.env

# Verify Kafka service
kubectl get svc my-cluster-kafka-external-bootstrap
```

### MongoDB Connection Issues

```bash
# Check MongoDB is running
kubectl get pods | grep mongodb

# ⭐ Query trực tiếp vào pod (không cần port-forward)
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  db.enriched_events.countDocuments()
"

# Nếu vẫn muốn dùng port-forward
kubectl port-forward svc/my-mongo-mongodb 27017:27017
kubectl port-forward svc/my-mongo-mongodb 27017:27017

# Test connection
mongosh mongodb://localhost:27017/bigdata_db --eval "db.runCommand({ ping: 1 })"
```

### Event Simulator Not Working

```bash
# Check .env file exists
cat config/.env

# Verify CSV file location
ls -lh data/raw/ecommerce_events_2019_oct.csv

# Test Kafka connectivity
python -c "from kafka import KafkaProducer; print('OK')"
```

## 🧹 Cleanup

```bash
# Delete all Kubernetes resources
kubectl delete -f kubernetes/spark-deployments.yaml
kubectl delete -f config/kafka-strimzi.yaml

# Or stop Minikube completely
minikube stop
minikube delete
```

## 📚 Detailed Documentation

- **[docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** - Complete step-by-step setup (12 phases)
- **[docs/TECHNICAL_DOCS.md](docs/TECHNICAL_DOCS.md)** - Architecture & technical details
- **[docs/README.md](docs/README.md)** - Detailed feature explanations

## 🎓 Academic Context

**Course:** IT4931 - Big Data Analytics  
**Topic:** Real-time Customer Journey Analytics  
**Technologies Demonstrated:**
- Distributed stream processing (Spark Structured Streaming)
- Message queuing (Apache Kafka)
- NoSQL databases (MongoDB)
- Container orchestration (Kubernetes)
- Machine Learning (MLlib)
- Data engineering best practices

## �� Team Members

For teammates cloning this project:
1. Follow the **Quick Start** section above
2. Read `docs/SETUP_GUIDE.md` for detailed explanations
3. Check `config/.env.example` for configuration options

## 📄 License

Academic project for IT4931 course.

---

**Need help?** Check the troubleshooting section above or see `docs/SETUP_GUIDE.md` for more details.
