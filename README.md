# Big Data Customer Journey Analytics

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Apache Spark 3.5.0](https://img.shields.io/badge/spark-3.5.0-orange.svg)](https://spark.apache.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Real-time e-commerce customer journey analytics system using Apache Spark, Kafka, and MongoDB.

## 📖 Overview

This project demonstrates a **production-ready big data analytics pipeline** for analyzing customer behavior in real-time. It processes millions of e-commerce events (views, carts, purchases) to generate insights about customer journeys, conversion funnels, and behavior patterns.

**Key Features:**
- ⚡ Real-time streaming with Spark Structured Streaming
- 📊 Complex windowed aggregations and stateful processing
- 🔗 Stream-static joins with dimension tables
- 🤖 Machine Learning (K-Means clustering, Random Forest)
- 🎯 Exactly-once semantics with checkpointing
- 📈 Analytics results in MongoDB

## 🏗️ Architecture

```
CSV Data (5.3GB) → Kafka → Spark Streaming → MongoDB
                              ↓
                      Batch ML Jobs
```

**Technology Stack:**
- **Apache Spark 3.5.0** - Stream & batch processing
- **Apache Kafka (Strimzi)** - Message broker
- **MongoDB (Bitnami)** - Analytics database
- **Kubernetes (Minikube)** - Container orchestration
- **Python 3.10+** - Application language

## 📁 Project Structure

```
BTL_IT4931/
├── app/                          # Application code
│   ├── config/                   # Configuration management
│   │   ├── settings.py          # Central settings
│   │   ├── kafka_config.py      # Kafka configuration
│   │   ├── mongodb_config.py    # MongoDB configuration
│   │   └── spark_config.py      # Spark configuration
│   ├── connectors/              # External system connectors
│   │   ├── kafka_connector.py   # Kafka read/write
│   │   └── mongodb_connector.py # MongoDB read/write
│   ├── models/                  # Data schemas
│   │   ├── event_schema.py      # Event data schemas
│   │   ├── product_schema.py    # Product catalog schemas
│   │   └── user_schema.py       # User dimension schemas
│   ├── processors/              # Data transformation logic
│   │   ├── event_enricher.py    # Event enrichment
│   │   ├── aggregator.py        # Aggregation logic
│   │   └── session_analyzer.py  # Session analysis
│   ├── jobs/                    # Spark jobs
│   │   ├── streaming/          
│   │   │   └── advanced_streaming.py  # Main streaming job
│   │   └── batch/
│   │       └── ml_analytics.py        # ML batch job
│   └── utils/                   # Utilities
│       ├── spark_factory.py     # Spark session factory
│       └── event_simulator.py   # Kafka event producer
├── deploy/                      # Deployment configurations
│   ├── docker/
│   │   └── Dockerfile          # Container image
│   ├── kubernetes/
│   │   └── base/               # K8s manifests
│   └── scripts/                # Deployment scripts
├── config/                      # Configuration files
│   ├── .env.example            # Environment template
│   └── .env                    # Local environment (git-ignored)
├── data/
│   ├── catalog/                # Dimension tables (CSV)
│   └── raw/                    # Raw event data (5.3GB CSV)
├── docs/                        # Documentation
├── tests/                       # Unit & integration tests
├── notebooks/                   # Jupyter notebooks for analysis
├── setup.py                     # Python package setup
├── Makefile                     # Development commands
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites

- **Docker** (20.10+)
- **Minikube** (v1.25+)
- **kubectl** (v1.25+)
- **Helm** (v3.0+)
- **Python 3.10+**
- **System**: 4 CPU cores, 8GB RAM, 20GB disk

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/minhngobka/BTL_IT4931.git
cd BTL_IT4931

# 2. Download dataset (5.3GB)
# Get 2019-Oct.csv from Kaggle:
# https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store
# Place it in: data/raw/ecommerce_events_2019_oct.csv

# 3. Install Python dependencies
make install

# 4. Set up configuration
make setup-env
# Edit config/.env with your settings

# 5. Start Minikube
make minikube-start

# 6. Deploy all components (Kafka, MongoDB, Spark)
make deploy

# 7. Start event simulator
make run-simulator
```

**⏱️ Total time:** ~25 minutes

## 💻 Usage

### Run Streaming Analytics

```bash
# Using Make
make run-streaming

# Or directly
python -m app.jobs.streaming.advanced_streaming
```

### Run ML Batch Job

```bash
# Using Make
make run-ml

# Or directly
python -m app.jobs.batch.ml_analytics
```

### Monitor Applications

```bash
# Check status
make status

# View streaming logs
make logs-streaming

# Access Spark UI
make port-forward-spark
# Open http://localhost:4040

# Query MongoDB
make query-mongo
```

## 📊 Data Flow

### Streaming Pipeline

1. **Event Simulator** reads CSV and produces to Kafka
2. **Spark Streaming** consumes from Kafka
3. **Event Enricher** joins events with product/user dimensions
4. **Aggregators** compute windowed metrics
5. **Session Analyzer** analyzes user journeys
6. Results written to MongoDB collections

### Batch ML Pipeline

1. **Load** enriched events from MongoDB
2. **Feature Engineering** creates user-level metrics
3. **K-Means** segments customers into clusters
4. **Random Forest** predicts customer churn
5. Results saved to MongoDB

## 🔧 Configuration

Configuration is managed through environment variables in `config/.env`:

```env
# Kafka
KAFKA_INTERNAL_BROKER=my-cluster-kafka-bootstrap.default.svc.cluster.local:9092
KAFKA_EXTERNAL_BROKER=192.168.49.2:31927
KAFKA_TOPIC=customer_events

# MongoDB
MONGODB_URI=mongodb://my-mongo-mongodb.default.svc.cluster.local:27017/
MONGODB_DATABASE=bigdata_db

# Simulator
CSV_FILE_PATH=data/raw/ecommerce_events_2019_oct.csv
CHUNK_SIZE=1000
SLEEP_TIME=0.01

# Spark
CHECKPOINT_BASE=/opt/spark/work-dir/checkpoints
SPARK_MASTER=local[*]
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Lint code
make lint

# Format code
make format
```

## 📖 Documentation

- **[USAGE.md](USAGE.md)** - Complete setup and usage guide
- **[TECHNICAL.md](TECHNICAL.md)** - Architecture and technical details

For quick reference, run `make help` to see all available commands.

## 🛠️ Development

### Using Make Commands

```bash
make help              # Show all available commands
make install-dev       # Install development dependencies
make format            # Format code with black
make lint              # Run linters
make test              # Run tests
make clean             # Clean generated files
make build-docker      # Build Docker image
make deploy            # Deploy all components
make undeploy          # Remove all deployments
```

### Code Structure

- **Modular design**: Separation of concerns (connectors, processors, jobs)
- **Configuration management**: Centralized settings
- **Type hints**: Throughout the codebase
- **Documentation**: Docstrings for all modules and functions

## 📈 Monitoring

### Kubernetes

```bash
# Pod status
kubectl get pods

# Service endpoints
kubectl get services

# Application logs
kubectl logs -f <pod-name>
```

### Spark UI

```bash
# Port forward Spark UI
kubectl port-forward deployment/spark-streaming-advanced 4040:4040
# Access: http://localhost:4040
```

### MongoDB

```bash
# Port forward MongoDB
kubectl port-forward svc/my-mongo-mongodb 27017:27017

# Query collections
mongosh mongodb://localhost:27017/bigdata_db
```

## 🐛 Troubleshooting

Common issues and solutions:

**Pods stuck in Pending/ImagePullBackOff:**
```bash
kubectl describe pod <pod-name>
docker build -t bigdata-spark:latest -f deploy/docker/Dockerfile .
minikube image load bigdata-spark:latest
kubectl rollout restart deployment/spark-streaming-advanced
```

**Kafka connection failed:**
```bash
minikube ip  # Update config/.env with this IP
kubectl get svc my-cluster-kafka-external-bootstrap
```

**MongoDB connection issues:**
```bash
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "db.enriched_events.countDocuments()"
```

See **USAGE.md** for more detailed troubleshooting.

## 🎓 Academic Context

**Course:** IT4931 - Big Data Analytics  
**Topic:** Real-time Customer Journey Analytics  
**Technologies Demonstrated:**
- Distributed stream processing
- Message queuing
- NoSQL databases
- Container orchestration
- Machine Learning

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

This is an academic project. For teammates:
1. Follow the code structure and conventions
2. Add tests for new features
3. Update documentation
4. Use the Makefile for common tasks

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Last Updated:** December 2025
