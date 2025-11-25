# 🚀 Quick Start - Run the Project

## Option 1: Automated Step-by-Step Guide (RECOMMENDED)

```bash
cd /home/tham/bigdata_project
./run_project_step_by_step.sh
```

This script will guide you through each phase with explanations and wait for your confirmation before proceeding.

---

## Option 2: Manual Steps

### Step 1: Setup Python Environment (2 minutes)

```bash
cd /home/tham/bigdata_project

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Generate Dimension Data (1 minute)

```bash
python generate_dimensions.py
```

This creates:
- `user_dimension.csv`
- `product_catalog.csv` (enhanced)
- `category_hierarchy.csv`

### Step 3: Start Minikube (3 minutes)

```bash
minikube start --driver=docker --cpus=4 --memory=8g --disk-size=20g
```

Wait until it says "Done! kubectl is now configured"

### Step 4: Deploy MongoDB (2 minutes)

```bash
# Add Helm repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install MongoDB
helm install my-mongo bitnami/mongodb --set auth.enabled=false

# Wait for it to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mongodb --timeout=300s
```

### Step 5: Deploy Kafka (3 minutes)

```bash
# Add Strimzi repo
helm repo add strimzi https://strimzi.io/charts/
helm repo update

# Install Strimzi operator
helm install strimzi-operator strimzi/strimzi-kafka-operator

# Wait for operator
kubectl wait --for=condition=ready pod -l name=strimzi-cluster-operator --timeout=300s

# Deploy Kafka cluster
kubectl apply -f kafka-combined.yaml

# Wait for Kafka
kubectl wait --for=condition=ready pod -l strimzi.io/name=my-cluster-kafka --timeout=300s
```

### Step 6: Build Docker Image (10 minutes)

```bash
# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Build image
docker build -t bigdata-spark:latest .
```

### Step 7: Deploy Spark Applications (1 minute)

```bash
kubectl apply -f k8s-spark-apps.yaml

# Check deployment
kubectl get pods
```

### Step 8: Update Simulator Configuration (1 minute)

```bash
# Get Kafka connection info
MINIKUBE_IP=$(minikube ip)
KAFKA_PORT=$(kubectl get service my-cluster-kafka-external-bootstrap -o jsonpath='{.spec.ports[0].nodePort}')

echo "Kafka Address: $MINIKUBE_IP:$KAFKA_PORT"
```

**Edit `simulator.py` line 11:**
```python
KAFKA_BROKER = '192.168.49.2:31927'  # Use your actual IP:Port
```

### Step 9: Run the Simulator

**Terminal 1:**
```bash
source venv/bin/activate
python simulator.py
```

You should see:
```
>>> Kết nối Kafka THÀNH CÔNG!
Sent: view - User: 123456
Sent: cart - User: 789012
```

### Step 10: Monitor Streaming

**Terminal 2:**
```bash
kubectl logs -f deployment/spark-streaming-advanced
```

You should see:
```
✓ Spark Session initialized
✓ Dimension tables loaded
✓ Connected to Kafka stream
✓ Epoch 0: Wrote X records to enriched_events
```

### Step 11: Access Spark UI (Optional)

**Terminal 3:**
```bash
kubectl port-forward deployment/spark-streaming-advanced 4040:4040
```

Open browser: http://localhost:4040

### Step 12: Run Batch ML Job (After 5-10 minutes)

**Terminal 4:**
```bash
kubectl create job spark-batch-manual --from=cronjob/spark-batch-ml-scheduled

# Watch progress
kubectl logs -f job/spark-batch-manual
```

### Step 13: Query Results in MongoDB

**Terminal 5:**
```bash
# Port-forward MongoDB
kubectl port-forward service/my-mongo-mongodb 27017:27017 &

# Connect
mongosh mongodb://localhost:27017

# In mongosh:
use bigdata_db

# View enriched events
db.enriched_events.find().limit(5).pretty()

# View aggregations
db.event_aggregations.find().sort({_id: -1}).limit(10)

# View session analytics
db.user_session_analytics.find().sort({total_events: -1}).limit(10)

# View customer segments
db.customer_segments.find()

# View churn predictions
db.churn_predictions.find({churn_prediction: 1}).limit(10)

# Count documents
db.getCollectionNames().forEach(function(col) {
    print(col + ": " + db[col].countDocuments());
})
```

---

## Verification Checklist

After deployment, verify everything is working:

```bash
# Check all pods are running
kubectl get pods

# Should see:
# ✓ my-mongo-mongodb-0                      1/1  Running
# ✓ my-cluster-kafka-0                      1/1  Running
# ✓ strimzi-cluster-operator-xxx            1/1  Running
# ✓ my-cluster-entity-operator-xxx          2/2  Running
# ✓ spark-streaming-advanced-xxx            1/1  Running
```

Run validation script:
```bash
./validate_setup.sh
```

---

## Common Issues and Quick Fixes

### Issue 1: "python: command not found"
```bash
# Use python3 instead
python3 -m venv venv
```

### Issue 2: Minikube won't start
```bash
# Delete and restart
minikube delete
minikube start --driver=docker --cpus=4 --memory=8g
```

### Issue 3: Kafka connection timeout
```bash
# Check Kafka service
kubectl get service | grep kafka

# Get correct port
kubectl get service my-cluster-kafka-external-bootstrap -o jsonpath='{.spec.ports[0].nodePort}'

# Update simulator.py with correct IP:Port
```

### Issue 4: Spark pod crashes
```bash
# Check logs
kubectl logs deployment/spark-streaming-advanced --previous

# If memory issue, increase limits:
kubectl edit deployment spark-streaming-advanced
# Change resources.limits.memory to "6Gi"
```

### Issue 5: No data in MongoDB
```bash
# Check if simulator is connected
# Look for "Kết nối Kafka THÀNH CÔNG!" message

# Check streaming logs
kubectl logs -f deployment/spark-streaming-advanced

# Restart streaming if needed
kubectl rollout restart deployment/spark-streaming-advanced
```

---

## Quick Commands Reference

### View Logs
```bash
# Streaming app
kubectl logs -f deployment/spark-streaming-advanced

# Batch job
kubectl logs -f job/spark-batch-manual

# Kafka
kubectl logs my-cluster-kafka-0

# MongoDB
kubectl logs my-mongo-mongodb-0
```

### Restart Components
```bash
# Restart streaming app
kubectl rollout restart deployment/spark-streaming-advanced

# Delete and recreate Kafka
kubectl delete -f kafka-combined.yaml
sleep 30
kubectl apply -f kafka-combined.yaml
```

### Check Status
```bash
# All pods
kubectl get pods

# All deployments
kubectl get deployments

# All services
kubectl get services

# Recent events
kubectl get events --sort-by='.lastTimestamp'
```

### Stop Everything
```bash
# Stop simulator (Ctrl+C)

# Delete K8s resources
kubectl delete -f k8s-spark-apps.yaml
kubectl delete -f kafka-combined.yaml
helm uninstall strimzi-operator
helm uninstall my-mongo

# Stop Minikube
minikube stop
```

---

## Time Estimates

| Phase | First Time | Subsequent |
|-------|-----------|------------|
| Python setup | 2 min | 30 sec |
| Generate data | 1 min | 1 min |
| Start Minikube | 3 min | 1 min |
| Deploy MongoDB | 2 min | 30 sec |
| Deploy Kafka | 3 min | 1 min |
| Build Docker | 10 min | 2 min (cached) |
| Deploy Spark | 1 min | 30 sec |
| **Total** | **~20-25 min** | **~6-7 min** |

---

## Data Flow Verification

To verify data is flowing correctly:

1. **Simulator** → Should show "Sent: view/cart/purchase"
2. **Kafka** → Should have messages (check with streaming logs)
3. **Streaming App** → Should show "Wrote X records"
4. **MongoDB** → Should have data in collections
5. **Batch Job** → Should complete with ML results

---

## Next Steps After Setup

1. **Let simulator run** for 5-10 minutes to accumulate data
2. **Monitor streaming logs** to see real-time processing
3. **Run batch ML job** to get segmentation and churn predictions
4. **Query MongoDB** to see results
5. **Access Spark UI** to see performance metrics

---

## Need Help?

1. Run: `./validate_setup.sh` to check system status
2. Check: `README_ADVANCED.md` for detailed documentation
3. See: `DEPLOYMENT_GUIDE.md` for troubleshooting
4. Use: `QUICK_REFERENCE.md` for command reference

---

## Ready to Start?

Run the automated guide:
```bash
./run_project_step_by_step.sh
```

Or follow the manual steps above!

**Good luck! 🚀**
