# 🚀 Quick Start Deployment Guide

## Complete Step-by-Step Instructions

### Phase 1: Environment Setup (15 minutes)

#### 1.1 Install Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io
sudo usermod -aG docker $USER
newgrp docker

# Install Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

# Install kubectl
sudo snap install kubectl --classic

# Install Helm
sudo snap install helm --classic

# Install Python dependencies
sudo apt install -y python3.10 python3-pip python3.10-venv
```

#### 1.2 Start Minikube

```bash
# Start with sufficient resources
minikube start --driver=docker --cpus=4 --memory=8g --disk-size=20g

# Enable addons (optional but useful)
minikube addons enable metrics-server
minikube addons enable dashboard

# Verify
kubectl get nodes
minikube status
```

---

### Phase 2: Data Preparation (10 minutes)

#### 2.1 Clone Repository

```bash
cd ~
git clone https://github.com/minhngobka/BTL_IT4931.git
cd BTL_IT4931
```

#### 2.2 Download Dataset

1. Go to: https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store
2. Download `2019-Oct.csv`
3. Place in project directory:
   ```bash
   # If downloaded to ~/Downloads
   mv ~/Downloads/2019-Oct.csv ~/BTL_IT4931/
   ```

#### 2.3 Generate Dimension Tables

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Generate dimension data
python generate_dimensions.py

# Verify files created
ls -lh *.csv
# Should see: 2019-Oct.csv, product_catalog.csv, user_dimension.csv, category_hierarchy.csv
```

---

### Phase 3: Infrastructure Deployment (20 minutes)

#### 3.1 Deploy MongoDB

```bash
# Add Bitnami Helm repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install MongoDB without authentication (for development)
helm install my-mongo bitnami/mongodb \
  --set auth.enabled=false \
  --set persistence.size=10Gi

# Wait for MongoDB to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mongodb --timeout=300s

# Verify
kubectl get pods | grep mongo
# Should show: my-mongo-mongodb-0  1/1  Running
```

#### 3.2 Deploy Kafka

```bash
# Add Strimzi Helm repository
helm repo add strimzi https://strimzi.io/charts/
helm repo update

# Install Strimzi Kafka Operator
helm install strimzi-operator strimzi/strimzi-kafka-operator

# Wait for operator to be ready
kubectl wait --for=condition=ready pod -l name=strimzi-cluster-operator --timeout=300s

# Deploy Kafka cluster
kubectl apply -f kafka-combined.yaml

# Wait for Kafka to be ready (this may take 2-3 minutes)
kubectl wait --for=condition=ready pod -l strimzi.io/name=my-cluster-kafka --timeout=300s

# Verify all components
kubectl get pods
# Should show:
# - strimzi-cluster-operator-xxx  1/1  Running
# - my-cluster-kafka-0  1/1  Running
# - my-cluster-entity-operator-xxx  2/2  Running
```

---

### Phase 4: Build and Deploy Spark Applications (15 minutes)

#### 4.1 Build Docker Image

```bash
# Configure Docker to use Minikube's daemon
eval $(minikube docker-env)

# Build image (this will take 5-10 minutes on first build)
docker build -t bigdata-spark:latest .

# Verify image
docker images | grep bigdata-spark
```

#### 4.2 Deploy Spark Applications

```bash
# Deploy all Spark applications
kubectl apply -f k8s-spark-apps.yaml

# Watch deployments start
kubectl get deployments -w

# Wait for streaming app to be ready
kubectl wait --for=condition=available deployment/spark-streaming-advanced --timeout=300s

# Check all pods
kubectl get pods
# Should include: spark-streaming-advanced-xxx  1/1  Running
```

#### 4.3 Verify Deployments

```bash
# Check all resources
kubectl get all

# View streaming logs
kubectl logs -f deployment/spark-streaming-advanced

# Should see output like:
# "Spark Session initialized"
# "Dimension tables loaded"
# "Connected to Kafka stream"
```

---

### Phase 5: Run the System (10 minutes)

#### 5.1 Get Kafka Connection Info

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

# Get Kafka NodePort
KAFKA_PORT=$(kubectl get service my-cluster-kafka-external-bootstrap -o jsonpath='{.spec.ports[0].nodePort}')
echo "Kafka Port: $KAFKA_PORT"

# Full Kafka address
echo "Kafka Bootstrap Server: $MINIKUBE_IP:$KAFKA_PORT"
```

#### 5.2 Update and Run Simulator

```bash
# Edit simulator.py and update the KAFKA_BROKER variable
# Line 11: KAFKA_BROKER = '<MINIKUBE_IP>:<KAFKA_PORT>'

# Example:
# KAFKA_BROKER = '192.168.49.2:31927'

# Open in editor
nano simulator.py
# or
vim simulator.py

# Run simulator
python simulator.py

# You should see:
# ">>> Kết nối Kafka THÀNH CÔNG!"
# "Sent: view - User: 123456"
# "Sent: cart - User: 789012"
# ...
```

#### 5.3 Monitor Streaming Processing

Open a new terminal:

```bash
# Terminal 2: Watch streaming logs
kubectl logs -f deployment/spark-streaming-advanced

# You should see:
# "✓ Epoch 0: Wrote X records to enriched_events"
# "✓ Epoch 1: Wrote Y records to event_aggregations"
```

#### 5.4 Access Spark UI

Open another terminal:

```bash
# Terminal 3: Port-forward Spark UI
kubectl port-forward deployment/spark-streaming-advanced 4040:4040

# Open browser: http://localhost:4040
# View:
# - Running queries
# - Processing times
# - DAG visualization
```

---

### Phase 6: Run Batch ML Analytics (15 minutes)

#### 6.1 Wait for Sufficient Data

```bash
# Let simulator run for at least 5-10 minutes to accumulate data
# Keep simulator running in Terminal 1

# Check data volume in MongoDB
kubectl port-forward service/my-mongo-mongodb 27017:27017 &

# Connect to MongoDB
mongosh mongodb://localhost:27017

# Check record counts
use bigdata_db
db.enriched_events.countDocuments()
# Should show: >10000 for good ML results

exit
```

#### 6.2 Run Batch Job

```bash
# Create batch job from CronJob template
kubectl create job spark-batch-manual --from=cronjob/spark-batch-ml-scheduled

# Watch job progress
kubectl get jobs -w

# View logs (wait for pod to start)
kubectl logs -f job/spark-batch-manual

# You should see:
# "Feature Engineering for Machine Learning"
# "✓ Computed features for X users"
# "Customer Segmentation with K-Means"
# "✓ Optimal clusters: k=4"
# "Churn Prediction with Random Forest"
# "✓ Model AUC-ROC: 0.XX"
```

---

### Phase 7: Query Results (10 minutes)

#### 7.1 MongoDB Queries

```bash
# Connect to MongoDB (if not already connected)
kubectl port-forward service/my-mongo-mongodb 27017:27017 &
mongosh mongodb://localhost:27017

use bigdata_db

# 1. View enriched events
db.enriched_events.find().limit(5).pretty()

# 2. View real-time aggregations
db.event_aggregations.find().sort({_id: -1}).limit(10)

# 3. View session analytics
db.user_session_analytics.find().sort({total_events: -1}).limit(10)

# 4. View conversion funnel
db.conversion_funnel.find().sort({_id: -1}).limit(5)

# 5. View customer segments
db.customer_segments.find()

# 6. View high-risk churn users
db.churn_predictions.find({churn_prediction: 1}).sort({churn_probability: -1}).limit(10)

# 7. View time series trends
db.time_series_analysis.find().sort({date: -1}).limit(10)

# 8. View statistical analysis
db.statistical_analysis.find()

# Get collection counts
db.getCollectionNames().forEach(function(collection) {
    print(collection + ": " + db[collection].countDocuments());
})
```

---

### Phase 8: Monitoring and Debugging

#### 8.1 Kubernetes Dashboard

```bash
# Start dashboard
minikube dashboard

# Opens browser with:
# - Pod status and logs
# - Resource usage
# - Deployment health
```

#### 8.2 Check Resource Usage

```bash
# View pod resource consumption
kubectl top pods

# View node resources
kubectl top nodes

# Describe problematic pod
kubectl describe pod <pod-name>
```

#### 8.3 View All Logs

```bash
# Streaming app
kubectl logs deployment/spark-streaming-advanced --tail=100

# Batch job
kubectl logs job/spark-batch-manual

# Kafka
kubectl logs my-cluster-kafka-0

# MongoDB
kubectl logs my-mongo-mongodb-0

# Follow logs in real-time
kubectl logs -f <pod-name>
```

---

## 🎯 Verification Checklist

Use this checklist to ensure everything is working:

- [ ] Minikube is running: `minikube status`
- [ ] MongoDB pod is Running: `kubectl get pods | grep mongo`
- [ ] Kafka pod is Running: `kubectl get pods | grep kafka`
- [ ] Spark streaming pod is Running: `kubectl get pods | grep spark-streaming`
- [ ] Simulator is sending events: Check simulator output
- [ ] Streaming is processing: Check streaming pod logs
- [ ] Data is in MongoDB: Query enriched_events collection
- [ ] Batch job completed: `kubectl get jobs`
- [ ] ML results available: Query customer_segments collection
- [ ] Spark UI accessible: http://localhost:4040

---

## 🐛 Common Issues and Solutions

### Issue 1: Minikube won't start

```bash
# Solution: Delete and recreate
minikube delete
minikube start --driver=docker --cpus=4 --memory=8g
```

### Issue 2: Docker build fails with "manifest not found"

```bash
# Solution: Pull base image explicitly
docker pull apache/spark:3.5.0-python3
eval $(minikube docker-env)
docker build -t bigdata-spark:latest .
```

### Issue 3: Kafka connection timeout in simulator

```bash
# Solution 1: Verify Kafka service
kubectl get service | grep kafka

# Solution 2: Check Kafka logs
kubectl logs my-cluster-kafka-0

# Solution 3: Recreate Kafka
kubectl delete -f kafka-combined.yaml
sleep 30
kubectl apply -f kafka-combined.yaml
```

### Issue 4: Spark streaming pod crashes

```bash
# Solution: Check logs for errors
kubectl logs deployment/spark-streaming-advanced --previous

# If memory issues, increase resources:
kubectl edit deployment spark-streaming-advanced
# Change: resources.limits.memory to "6Gi"
```

### Issue 5: No data in MongoDB

```bash
# Check if simulator is running and connected
# Check streaming pod logs for errors
kubectl logs -f deployment/spark-streaming-advanced

# Restart streaming deployment
kubectl rollout restart deployment/spark-streaming-advanced
```

---

## 🧹 Cleanup

### Stop Everything

```bash
# Stop simulator (Ctrl+C in simulator terminal)

# Delete Kubernetes resources
kubectl delete -f k8s-spark-apps.yaml
kubectl delete -f kafka-combined.yaml
helm uninstall strimzi-operator
helm uninstall my-mongo

# Stop Minikube
minikube stop

# (Optional) Delete Minikube cluster
minikube delete
```

### Resume Later

```bash
# Start Minikube
minikube start

# Redeploy infrastructure
helm install my-mongo bitnami/mongodb --set auth.enabled=false
helm install strimzi-operator strimzi/strimzi-kafka-operator
kubectl apply -f kafka-combined.yaml

# Wait for pods to be ready
kubectl get pods -w

# Redeploy applications
kubectl apply -f k8s-spark-apps.yaml

# Continue from Phase 5
```

---

## 📞 Support

If you encounter issues:

1. Check the **Troubleshooting** section in README_ADVANCED.md
2. Review pod logs: `kubectl logs <pod-name>`
3. Check Kubernetes events: `kubectl get events --sort-by='.lastTimestamp'`
4. Consult course materials
5. Contact teaching team

---

**Deployment time: ~1.5 hours (first time)**

**Subsequent deployments: ~20 minutes**

Good luck with your project! 🚀
