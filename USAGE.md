# Complete Setup Guide

Step-by-step instructions to deploy the Big Data Customer Journey project.

---

## ⏱️ Timeline

| Phase | Time | Description |
|-------|------|-------------|
| Prerequisites | 15 min | Install Docker, Minikube, kubectl, Helm, Python |
| Clone & Dataset | 10 min | Download code and 2019-Oct.csv (5.3GB) |
| Python Setup | 2 min | Create venv and install dependencies |
| Minikube Start | 3 min | Launch Kubernetes cluster |
| **Automated Deployment** | **15 min** | **Run script to deploy everything** |
| Configure | 2 min | Set environment variables |
| Run Simulator | Ongoing | Send events to process |

**Total: ~25-30 minutes**

---

## 📋 Prerequisites

### Required Software

**1. Docker** (container runtime)
```bash
sudo apt update
sudo apt install docker.io -y
sudo usermod -aG docker $USER
# Log out and log back in for group changes to take effect
```

**2. Minikube** (local Kubernetes)
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64
```

**3. kubectl** (Kubernetes CLI)
```bash
sudo snap install kubectl --classic
```

**4. Helm** (Kubernetes package manager)
```bash
sudo snap install helm --classic
```

**5. Python 3.10+**
```bash
sudo apt install python3.10 python3.10-venv python3-pip -y
```

### Verify Installation
```bash
docker --version      # Docker version 20.10+
minikube version      # minikube version v1.25+
kubectl version --client  # Client Version: v1.25+
helm version          # version.BuildInfo{Version:"v3.x.x"
python3 --version     # Python 3.10+
```

---

## 🚀 Step-by-Step Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/minhngobka/BTL_IT4931.git
cd BTL_IT4931
```

### Step 2: Download Dataset

**Option A: Manual Download (Recommended)**

1. Visit: https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store
2. Download **2019-Oct.csv** (5.3GB)
3. Move to project directory:
   ```bash
   mv ~/Downloads/2019-Oct.csv /path/to/BTL_IT4931/
   ```

**Option B: Kaggle API**
```bash
pip install kaggle
# Get API key from https://www.kaggle.com/settings (Create New API Token)
# Move kaggle.json to ~/.kaggle/
kaggle datasets download -d mkechinov/ecommerce-behavior-data-from-multi-category-store
unzip ecommerce-behavior-data-from-multi-category-store.zip
mv 2019-Oct.csv .
rm ecommerce-behavior-data-from-multi-category-store.zip
```

**Verify:**
```bash
ls -lh 2019-Oct.csv
# Should show: ~5.3G file
```

### Step 3: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# The file will be updated after Minikube starts
# (Step 6 will provide the correct values)
```

### Step 5: Start Minikube

```bash
# Start with sufficient resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify
minikube status
# Should show: host, kubelet, apiserver all "Running"
```

**If Minikube fails to start:**
```bash
# Clean previous installation
minikube delete

# Try again
minikube start --cpus=4 --memory=8192 --driver=docker

# Or increase resources if you have them
minikube start --cpus=6 --memory=10240 --driver=docker
```

### Step 6: Run Automated Deployment Script

```bash
# Make executable
chmod +x run_project_step_by_step.sh

# Run
./run_project_step_by_step.sh
```

**The script will:**

1. ✅ **Check prerequisites** (Docker, kubectl, Minikube running)
2. ✅ **Verify Python environment** (skip if already done)
3. ✅ **Generate dimension data** (`generate_dimensions.py`)
4. ✅ **Deploy MongoDB** via Helm (Bitnami chart)
5. ✅ **Deploy Kafka** via Helm (Strimzi operator)
6. ✅ **Build Docker image** (`bigdata-spark:latest`)
7. ✅ **Deploy Spark applications** (streaming + batch)
8. ✅ **Create Kafka topic** (`customer_events`)
9. ✅ **Show connection details**
10. ✅ **Validation checks**

**During deployment:**
- Press **Enter** at each phase to continue
- Script is idempotent (safe to re-run)
- If a component exists, it will be skipped
- Logs show progress and any issues

### Step 7: Update Environment Variables

After deployment completes, update `.env`:

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

# Get Kafka NodePort
KAFKA_PORT=$(kubectl get service my-cluster-kafka-external-bootstrap -o jsonpath='{.spec.ports[0].nodePort}')
echo "Kafka Port: $KAFKA_PORT"

# Edit .env file
nano .env  # or vim, code, gedit, etc.
```

**Update these lines:**
```env
KAFKA_EXTERNAL_BROKER=192.168.49.2:31927  # Use your MINIKUBE_IP:KAFKA_PORT
MINIKUBE_IP=192.168.49.2                   # Use your MINIKUBE_IP
```

**Or use sed to update automatically:**
```bash
sed -i "s/KAFKA_EXTERNAL_BROKER=.*/KAFKA_EXTERNAL_BROKER=$MINIKUBE_IP:$KAFKA_PORT/" .env
sed -i "s/MINIKUBE_IP=.*/MINIKUBE_IP=$MINIKUBE_IP/" .env
```

### Step 8: Verify Deployment

```bash
# Check all pods are running
kubectl get pods

# Expected output (all Running):
# my-mongo-mongodb-xxx             1/1     Running
# my-cluster-my-pool-0             1/1     Running
# spark-streaming-advanced-xxx     1/1     Running
# strimzi-cluster-operator-xxx     1/1     Running

# Check services
kubectl get services | grep -E 'mongo|kafka|spark'

# Run validation script (optional)
./validate_setup.sh
```

### Step 9: Run the Simulator

```bash
# Ensure venv is active
source venv/bin/activate

# Start sending events
python simulator.py
```

**You should see:**
```
Đang kết nối tới Kafka Broker tại 192.168.49.2:31927...
>>> Kết nối Kafka THÀNH CÔNG!
Bắt đầu đọc file: 2019-Oct.csv (chunksize=1000)

--- Gửi 1000 sự kiện ---
Sent: view - User: 541312140
Sent: view - User: 554748717
Sent: cart - User: 551377651
Sent: purchase - User: 543272936
...
```

**Stop with:** Ctrl+C

### Step 10: Monitor Processing

**In a new terminal, watch Spark logs:**
```bash
kubectl logs -f deployment/spark-streaming-advanced
```

**Look for:**
```
✓ Epoch 1: Wrote 1568 records to enriched_events
✓ Epoch 2: Wrote 757 records to user_session_analytics
✓ Epoch 3: Wrote 12 records to conversion_funnel
```

### Step 11: Query MongoDB Results

**Port-forward MongoDB:**
```bash
kubectl port-forward service/my-mongo-mongodb 27017:27017 &
```

**Connect and query:**
```bash
mongosh mongodb://localhost:27017
```

**In mongosh:**
```javascript
use bigdata_db

// Count records
db.enriched_events.countDocuments()        // ~20,000+
db.user_session_analytics.countDocuments() // ~8,000+
db.conversion_funnel.countDocuments()      // ~100+
db.event_aggregations.countDocuments()     // ~4,000+

// Sample enriched event
db.enriched_events.findOne()

// Session with purchase
db.user_session_analytics.findOne({purchase_count: {$gt: 0}})

// Conversion rates
db.conversion_funnel.find().limit(5).pretty()
```

### Step 12: Access Spark UI

```bash
# Port-forward Spark UI
kubectl port-forward service/spark-streaming-svc 4040:4040
```

**Open browser:** http://localhost:4040

**You'll see:**
- Active streaming queries
- Batch processing times
- DAG visualizations
- Executors & storage info

---

## 🤖 Optional: Run Batch ML Job

The system includes a scheduled batch job (runs every 6 hours). To trigger manually:

```bash
# Create job from CronJob template
kubectl create job spark-batch-manual --from=cronjob/spark-batch-ml-scheduled

# Watch logs
kubectl logs -f job/spark-batch-manual
```

**This performs:**
- K-Means customer segmentation (4 clusters)
- Random Forest churn prediction
- Time series analysis (hourly/daily patterns)
- Statistical analysis (correlations)

**Results written to MongoDB:**
```javascript
use bigdata_db
db.customer_segments.find().limit(5)      // Cluster assignments
db.churn_predictions.find().limit(5)      // Churn probabilities
db.time_series_analysis.find().limit(5)   // Temporal patterns
db.statistical_analysis.findOne()         // Correlation matrix
```

---

## 🛠️ Troubleshooting

### Simulator Can't Connect to Kafka

**Symptom:** `NoBrokersAvailable` error

**Solution:**
```bash
# 1. Verify Kafka is running
kubectl get pods | grep kafka
# Should show: my-cluster-my-pool-0 (Running)

# 2. Check external service
kubectl get service my-cluster-kafka-external-bootstrap
# Note the NodePort (e.g., 31927)

# 3. Update .env with correct values
MINIKUBE_IP=$(minikube ip)
KAFKA_PORT=$(kubectl get svc my-cluster-kafka-external-bootstrap -o jsonpath='{.spec.ports[0].nodePort}')
echo "Update .env: KAFKA_EXTERNAL_BROKER=$MINIKUBE_IP:$KAFKA_PORT"
```

### Pods Stuck in "Pending" State

**Symptom:** Pods don't start, stay in Pending

**Solution:**
```bash
# Check why
kubectl describe pod <pod-name>

# Usually insufficient resources
minikube stop
minikube delete
minikube start --cpus=4 --memory=10240  # Increase if possible

# Re-run deployment
./run_project_step_by_step.sh
```

### Docker Build Fails

**Symptom:** Error building bigdata-spark:latest

**Solution:**
```bash
# Ensure using Minikube's Docker daemon
eval $(minikube docker-env)

# Verify
docker ps  # Should show Minikube containers

# Rebuild
docker build -t bigdata-spark:latest .

# Check image exists
docker images | grep bigdata-spark
```

### Streaming Pod Crashes/Restarts

**Symptom:** spark-streaming-advanced pod keeps restarting

**Solution:**
```bash
# Check logs for errors
kubectl logs spark-streaming-advanced-xxx

# Common issues:
# 1. Kafka topic doesn't exist
kubectl exec -it my-cluster-my-pool-0 -- bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list
# Should show: customer_events

# If missing, create it:
kubectl exec -it my-cluster-my-pool-0 -- bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --create \
  --topic customer_events --partitions 3 --replication-factor 1

# 2. Resource limits too low - increase in k8s-spark-apps.yaml
# 3. Checkpoint corruption - delete checkpoints:
kubectl exec -it spark-streaming-advanced-xxx -- rm -rf /opt/spark/work-dir/checkpoints/*
kubectl delete pod -l app=spark-streaming  # Force restart
```

### MongoDB Connection Refused

**Symptom:** Can't connect via mongosh

**Solution:**
```bash
# 1. Check MongoDB is running
kubectl get pods | grep mongo
# Should show: my-mongo-mongodb-xxx (Running)

# 2. Verify port-forward
kubectl port-forward service/my-mongo-mongodb 27017:27017

# 3. In another terminal, connect
mongosh mongodb://localhost:27017

# 4. If still fails, check MongoDB logs
kubectl logs my-mongo-mongodb-xxx
```

### Minikube Won't Start

**Symptom:** Various Minikube startup errors

**Solution:**
```bash
# Clean slate
minikube delete
rm -rf ~/.minikube

# Check system requirements
# - VT-x/AMD-v virtualization enabled in BIOS
# - At least 4 CPU cores and 8GB RAM free

# Try different driver
minikube start --cpus=4 --memory=8192 --driver=docker
# Or
minikube start --cpus=4 --memory=8192 --driver=virtualbox

# Check status
minikube status
```

### "Image Pull" Errors

**Symptom:** Pods fail with ImagePullBackOff

**Solution:**
```bash
# For bigdata-spark:latest (local image)
# Ensure image was built in Minikube's Docker
eval $(minikube docker-env)
docker images | grep bigdata-spark

# If missing
docker build -t bigdata-spark:latest .

# For external images (MongoDB, Kafka)
# Check internet connection and try again
kubectl delete pod <failing-pod>
# It will recreate and try pulling again
```

---

## 🧹 Cleanup

### Stop Services (Keep Data)
```bash
# Stop simulator (Ctrl+C in terminal)

# Stop port-forwards (Ctrl+C in their terminals)

# Stop Minikube
minikube stop
```

### Full Cleanup (Delete Everything)
```bash
# Stop Minikube
minikube stop

# Delete cluster
minikube delete

# Remove Python venv
deactivate
rm -rf venv/

# Remove Docker images (optional)
eval $(minikube docker-env)
docker rmi bigdata-spark:latest
```

### Start Fresh
```bash
minikube start --cpus=4 --memory=8192
./run_project_step_by_step.sh
```

---

## 📊 Expected Data Flow

**After 5 minutes of simulator running:**

1. **Kafka Topic:**
   - ~2,000 events/minute ingested
   - 3 partitions for parallelism

2. **Spark Streaming:**
   - Processes micro-batches every 5-10 seconds
   - Enriches with product catalog
   - Aggregates by windows and sessions
   - Writes to MongoDB

3. **MongoDB Collections:**
   - enriched_events: ~20,000 records
   - user_session_analytics: ~8,000 sessions
   - conversion_funnel: ~100 time windows
   - event_aggregations: ~4,000 aggregations

4. **Batch ML (manual trigger):**
   - customer_segments: Cluster assignments
   - churn_predictions: Risk scores
   - time_series_analysis: Patterns
   - statistical_analysis: Correlations

---

## 🎯 Success Checklist

- [ ] All prerequisites installed and verified
- [ ] Repository cloned
- [ ] 2019-Oct.csv downloaded (5.3GB)
- [ ] Python venv created and activated
- [ ] Dependencies installed from requirements.txt
- [ ] `.env` file configured with correct IP:Port
- [ ] Minikube started (4 CPUs, 8GB RAM)
- [ ] Deployment script completed successfully
- [ ] All pods showing "Running" status
- [ ] Kafka topic `customer_events` exists
- [ ] Simulator connects and sends events
- [ ] Spark logs show batches processing
- [ ] MongoDB collections have data
- [ ] Spark UI accessible on port 4040

---

## 📚 Next Steps

- **Explore data:** Connect to MongoDB and run queries
- **Run ML job:** Trigger batch analytics
- **Monitor performance:** Check Spark UI metrics
- **Understand architecture:** Read [TECHNICAL_DOCS.md](TECHNICAL_DOCS.md)
- **Modify code:** Edit streaming_app_advanced.py and rebuild

---

**Need more details?** See [TECHNICAL_DOCS.md](TECHNICAL_DOCS.md) for architecture and feature explanations.
