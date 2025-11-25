# ⚡ Quick Reference Guide

## 🚀 Fast Commands Reference

### Project Setup (First Time)

```bash
# 1. Generate dimension data
python generate_dimensions.py

# 2. Start Minikube
minikube start --driver=docker --cpus=4 --memory=8g

# 3. Deploy MongoDB
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install my-mongo bitnami/mongodb --set auth.enabled=false

# 4. Deploy Kafka
helm repo add strimzi https://strimzi.io/charts/
helm install strimzi-operator strimzi/strimzi-kafka-operator
kubectl apply -f kafka-combined.yaml

# 5. Build and deploy Spark apps
eval $(minikube docker-env)
docker build -t bigdata-spark:latest .
kubectl apply -f k8s-spark-apps.yaml

# 6. Validate everything
./validate_setup.sh
```

---

## 🔍 Monitoring Commands

```bash
# View all pods
kubectl get pods

# Stream logs
kubectl logs -f deployment/spark-streaming-advanced

# Spark UI (then open http://localhost:4040)
kubectl port-forward deployment/spark-streaming-advanced 4040:4040

# MongoDB access (then open http://localhost:27017)
kubectl port-forward service/my-mongo-mongodb 27017:27017

# View all resources
kubectl get all

# Recent events
kubectl get events --sort-by='.lastTimestamp' | tail -20
```

---

## 📊 MongoDB Queries

```javascript
// Connect
mongosh mongodb://localhost:27017

// Switch to database
use bigdata_db

// View collections
show collections

// Count documents
db.enriched_events.countDocuments()
db.customer_segments.countDocuments()
db.churn_predictions.countDocuments()

// Sample queries
db.enriched_events.find().limit(5)
db.event_aggregations.find().sort({_id: -1}).limit(10)
db.customer_segments.find()
db.churn_predictions.find({churn_prediction: 1}).limit(10)

// Aggregation pipeline
db.enriched_events.aggregate([
  {$group: {_id: "$event_type", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

---

## 🎯 Running Jobs

```bash
# Run simulator
python simulator.py

# Create manual batch job
kubectl create job spark-batch-manual --from=cronjob/spark-batch-ml-scheduled

# Check job status
kubectl get jobs

# View job logs
kubectl logs job/spark-batch-manual
```

---

## 🐛 Troubleshooting

```bash
# Restart streaming
kubectl rollout restart deployment/spark-streaming-advanced

# Delete and recreate Kafka
kubectl delete -f kafka-combined.yaml
sleep 30
kubectl apply -f kafka-combined.yaml

# View pod details
kubectl describe pod <pod-name>

# Check resource usage
kubectl top pods
kubectl top nodes

# Clear checkpoints (development only!)
kubectl exec -it <spark-pod> -- rm -rf /opt/spark/work-dir/checkpoints/*

# Rebuild Docker image
eval $(minikube docker-env)
docker build -t bigdata-spark:latest . --no-cache
```

---

## 📁 Key File Locations

| File | Purpose |
|------|---------|
| `streaming_app_advanced.py` | Main streaming application |
| `batch_analytics_ml.py` | ML batch analytics |
| `k8s-spark-apps.yaml` | Kubernetes deployments |
| `README_ADVANCED.md` | Complete documentation |
| `FEATURES_MAPPING.md` | Requirements coverage |
| `validate_setup.sh` | System validation |

---

## 🔧 Configuration Files

```bash
# Edit Spark config
vim k8s-spark-apps.yaml

# Edit Kafka config
vim kafka-combined.yaml

# Update simulator Kafka address
vim simulator.py
# Change line 11: KAFKA_BROKER = '<IP>:<PORT>'
```

---

## 📈 Get Kafka Address

```bash
MINIKUBE_IP=$(minikube ip)
KAFKA_PORT=$(kubectl get service my-cluster-kafka-external-bootstrap -o jsonpath='{.spec.ports[0].nodePort}')
echo "Kafka Address: $MINIKUBE_IP:$KAFKA_PORT"
```

---

## 🧹 Cleanup

```bash
# Delete applications
kubectl delete -f k8s-spark-apps.yaml

# Delete Kafka
kubectl delete -f kafka-combined.yaml

# Uninstall Helm releases
helm uninstall my-mongo
helm uninstall strimzi-operator

# Stop Minikube
minikube stop

# Delete Minikube (complete cleanup)
minikube delete
```

---

## 📊 Verification Checklist

```bash
# Run validation script
./validate_setup.sh

# Or manual checks:
minikube status                              # Should be "Running"
kubectl get pods                             # All should be "Running"
kubectl logs deployment/spark-streaming-advanced  # No errors
mongosh mongodb://localhost:27017            # Can connect
# use bigdata_db
# db.enriched_events.countDocuments()       # > 0
```

---

## 🎓 Demo Flow

```bash
# 1. Show architecture
cat ARCHITECTURE_COMPARISON.md | head -100

# 2. Show requirements coverage
cat FEATURES_MAPPING.md | grep "✅"

# 3. Validate system
./validate_setup.sh

# 4. Show streaming logs
kubectl logs -f deployment/spark-streaming-advanced

# 5. Open Spark UI
kubectl port-forward deployment/spark-streaming-advanced 4040:4040
# Open: http://localhost:4040

# 6. Query MongoDB
kubectl port-forward service/my-mongo-mongodb 27017:27017
mongosh mongodb://localhost:27017
use bigdata_db
db.enriched_events.find().limit(5).pretty()

# 7. Run batch ML job
kubectl create job demo-batch --from=cronjob/spark-batch-ml-scheduled
kubectl logs -f job/demo-batch
```

---

## 📱 Useful Aliases

Add to `~/.bashrc`:

```bash
# Kubernetes shortcuts
alias k='kubectl'
alias kgp='kubectl get pods'
alias klf='kubectl logs -f'
alias kdp='kubectl describe pod'
alias kge='kubectl get events --sort-by=.lastTimestamp'

# Project specific
alias spark-logs='kubectl logs -f deployment/spark-streaming-advanced'
alias spark-ui='kubectl port-forward deployment/spark-streaming-advanced 4040:4040'
alias mongo-ui='kubectl port-forward service/my-mongo-mongodb 27017:27017'
alias validate='cd ~/bigdata_project && ./validate_setup.sh'

# Minikube
alias mk='minikube'
alias mkstart='minikube start --driver=docker --cpus=4 --memory=8g'
```

---

## 🆘 Emergency Recovery

```bash
# If everything is broken
kubectl delete -f k8s-spark-apps.yaml
kubectl delete -f kafka-combined.yaml
helm uninstall my-mongo
helm uninstall strimzi-operator
minikube delete

# Then restart from scratch
minikube start --driver=docker --cpus=4 --memory=8g
# ... follow setup steps
```

---

## 📞 Support Resources

| Issue | Document | Section |
|-------|----------|---------|
| Deployment problems | `DEPLOYMENT_GUIDE.md` | Phase-by-phase |
| Kafka connection | `README_ADVANCED.md` | Troubleshooting |
| Spark crashes | `README_ADVANCED.md` | Troubleshooting |
| MongoDB issues | `README_ADVANCED.md` | Troubleshooting |
| Feature questions | `FEATURES_MAPPING.md` | All |
| Architecture | `ARCHITECTURE_COMPARISON.md` | All |

---

## 🎯 Success Indicators

✅ All pods Running  
✅ Simulator sending events  
✅ Streaming processing data  
✅ Data appearing in MongoDB  
✅ Spark UI accessible  
✅ No errors in logs  
✅ Batch job completes successfully  
✅ ML results in database  

---

**Keep this file handy for quick reference!**

*For detailed instructions, see `DEPLOYMENT_GUIDE.md`*
