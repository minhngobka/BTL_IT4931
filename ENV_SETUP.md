# Environment Configuration Guide

## Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Update values in `.env` based on your environment:**
   ```bash
   # Get Minikube IP
   minikube ip
   
   # Get Kafka NodePort
   kubectl get service my-cluster-kafka-external-bootstrap
   
   # Update KAFKA_EXTERNAL_BROKER in .env with: <MINIKUBE_IP>:<NODEPORT>
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_EXTERNAL_BROKER` | Kafka external NodePort address | `192.168.49.2:31927` |
| `KAFKA_TOPIC` | Kafka topic name for events | `customer_events` |
| `MONGODB_HOST` | MongoDB host (for port-forwarding) | `localhost` |
| `MONGODB_PORT` | MongoDB port | `27017` |
| `MONGODB_DATABASE` | MongoDB database name | `bigdata_db` |
| `CSV_FILE_PATH` | Path to input CSV file | `2019-Oct.csv` |
| `CHUNK_SIZE` | Number of records per batch | `1000` |
| `SLEEP_TIME` | Delay between sends (seconds) | `0.01` |
| `MINIKUBE_IP` | Minikube cluster IP | `192.168.49.2` |

## Usage

The `.env` file is automatically loaded by:
- `simulator.py` - Event data simulator
- Any Python scripts using `python-dotenv`

**Note:** The `.env` file is in `.gitignore` to prevent committing local configuration or secrets.

## For Different Environments

**Local Development:**
```env
KAFKA_EXTERNAL_BROKER=192.168.49.2:31927
MONGODB_HOST=localhost
```

**Inside Kubernetes (if running Python scripts as Jobs):**
```env
KAFKA_EXTERNAL_BROKER=my-cluster-kafka-bootstrap.default.svc.cluster.local:9092
MONGODB_HOST=my-mongo-mongodb.default.svc.cluster.local
```

**Production:**
```env
KAFKA_EXTERNAL_BROKER=kafka.production.example.com:9092
MONGODB_HOST=mongodb.production.example.com
# Add authentication credentials here
```
