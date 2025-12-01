# Big Data Customer Journey Analytics

Real-time e-commerce customer journey analytics system using Apache Spark, Kafka, and MongoDB.

## About This Project

This project demonstrates a **real-time big data analytics pipeline** for analyzing customer behavior in an e-commerce platform. It processes millions of events (views, carts, purchases) in real-time to generate insights about customer journeys, conversion funnels, and behavior patterns.

**Key Features:**
- ⚡ **Real-time streaming** with Apache Spark Structured Streaming
- 📊 **Complex aggregations** (windowed, stateful, sessionization)
- 🔗 **Stream-static joins** with product catalogs
- 🤖 **Machine Learning** (K-Means clustering, Random Forest classification)
- 🎯 **Exactly-once semantics** with checkpointing
- 📈 **Analytics dashboard** via MongoDB queries

## Architecture

```
CSV Data (5.3GB) → Kafka → Spark Streaming → MongoDB
                              ↓
                      Batch ML Jobs (6 hours)
```
## Setup
```
# Setup Docker
docker-compose up --build

# Download dataset (5.3GB)
# Get 2019-Oct.csv from: https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store
# Place it in: data/raw/2019_Oct.csv

```
## Usage
```
# Đẩy data vào Kafka sử dụng \kafka\producers\csv_producer.py
python3 csv_producer.py
# Hiển thị data producer gửi vào Kafka 
docker exec -it kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic user_behavior_events --from-beginning

# Đẩy data từ Kafka vào Spark
docker exec -it spark-app python src/main.py

# Kiểm tra logs:
# Kiểm tra Spark Master
docker logs spark-master

# Kiểm tra Spark Worker
docker logs spark-worker

# Kiểm tra Kafka
docker logs kafka

# Kiểm tra Spark App
docker logs -f spark-app
```
Truy cập Web UI:
Spark Master: http://localhost:8080
Spark Worker: http://localhost:8081
