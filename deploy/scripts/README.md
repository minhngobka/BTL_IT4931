# Deployment Scripts

Scripts để deploy và monitor User Behavior Classification Pipeline.

---

## 📁 Available Scripts

### 🚀 Main Deployment

#### `deploy_all.sh`
**One-command deployment** cho toàn bộ hệ thống.

```bash
bash deploy/scripts/deploy_all.sh
```

**Deploys:**
- ✅ Minikube cluster
- ✅ MongoDB
- ✅ Kafka (Strimzi)
- ✅ Spark Streaming
- ✅ Prometheus
- ✅ Grafana
- ✅ MongoDB Exporter
- ✅ Spark UI

**Phases:**
1. Prerequisites check
2. Python environment setup
3. Data preparation
4. Kubernetes check
5. Start Minikube
6. Deploy MongoDB
7. Deploy Kafka
8. Build Docker image
9. Deploy Spark applications
10. Deploy monitoring stack
11. Setup port-forwards
12. Get Kafka connection info
13. Verify deployment

**Duration:** ~15-20 minutes (first run)

---

### 📊 Monitoring Scripts

#### `setup_monitoring.sh`
Deploy và khởi động monitoring stack với port-forwards.

```bash
bash deploy/scripts/setup_monitoring.sh
```

**Features:**
- Deploy Prometheus, Grafana, MongoDB Exporter
- Auto port-forward to localhost
- Open dashboards in browser (if `$BROWSER` set)
- Pre-configured User Behavior Classification dashboard

**Access:**
- Grafana: http://localhost:3000 (admin/admin123)
- Prometheus: http://localhost:9090
- Spark UI: http://localhost:4040

---

#### `monitor_streaming.sh`
Interactive monitoring menu với nhiều options.

```bash
bash deploy/scripts/monitor_streaming.sh
```

**Menu Options:**
1. View Spark Application Logs
2. View Streaming Query Status
3. View MongoDB Collections
4. View Segment Distribution (Live)
5. Open Spark UI (port-forward)
6. Open Grafana Dashboard
7. View Prometheus Metrics
8. Monitor All (tail logs)
9. Exit

**Best for:** Interactive debugging và real-time monitoring

---

#### `view_metrics.sh`
Quick CLI metrics view không cần UI.

```bash
bash deploy/scripts/view_metrics.sh
```

**Shows:**
- 🎯 Segment distribution với ASCII charts
- 💰 Revenue by segment
- 📈 Conversion funnel rates
- ⏱️ Recent sessions
- 📊 Summary statistics

**Best for:** Quick checks, CI/CD pipelines, terminal-only environments

---

## 🎯 Quick Start Workflow

### 1. Initial Deployment
```bash
# Deploy everything
bash deploy/scripts/deploy_all.sh

# Wait for completion (15-20 min)
# Port-forwards will be automatically started
```

### 2. Access Monitoring
```bash
# Option A: Use already port-forwarded services
open http://localhost:3000  # Grafana
open http://localhost:4040  # Spark UI

# Option B: Restart port-forwards if needed
bash deploy/scripts/setup_monitoring.sh
```

### 3. Generate Test Data
```bash
# Update Kafka address in config/.env first
python -m app.utils.test_behavior_generator
```

### 4. Monitor Results
```bash
# Option A: Interactive menu
bash deploy/scripts/monitor_streaming.sh

# Option B: Quick CLI view
bash deploy/scripts/view_metrics.sh

# Option C: Grafana dashboard
open http://localhost:3000
```

---

## 🛠️ Common Tasks

### Restart Spark Streaming
```bash
kubectl rollout restart deployment/spark-streaming-advanced
```

### View Spark Logs
```bash
kubectl logs -f deployment/spark-streaming-advanced
```

### Scale Spark
```bash
kubectl scale deployment/spark-streaming-advanced --replicas=2
```

### Query MongoDB Directly
```bash
MONGO_POD=$(kubectl get pod -l app.kubernetes.io/name=mongodb -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $MONGO_POD -- mongosh bigdata
```

### Restart Port-Forwards
```bash
# Kill all existing
pkill -f 'port-forward'

# Restart monitoring stack
bash deploy/scripts/setup_monitoring.sh
```

---

## 🚨 Troubleshooting

### Port-Forward Not Working

**Problem:** Can't access http://localhost:3000

**Solution:**
```bash
# Check if port-forward is running
ps aux | grep port-forward

# Restart
pkill -f 'port-forward'
bash deploy/scripts/setup_monitoring.sh
```

### Spark UI Shows 404

**Problem:** http://localhost:4040 returns 404

**Solution:**
```bash
# Check if Spark pod is running
kubectl get pods | grep spark-streaming

# Check if job is running
kubectl logs deployment/spark-streaming-advanced | grep "Starting"

# Port-forward directly to pod
SPARK_POD=$(kubectl get pod -l app=spark-streaming -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward $SPARK_POD 4040:4040
```

### Grafana Dashboard Empty

**Problem:** Dashboard shows "No data"

**Solution:**
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Check if metrics are being scraped
curl -s http://localhost:8080/metrics | grep spark_streaming

# Verify MongoDB data exists
bash deploy/scripts/view_metrics.sh
```

### MongoDB Pod Not Ready

**Problem:** MongoDB pod stuck in `Pending` or `CrashLoopBackOff`

**Solution:**
```bash
# Check pod status
kubectl describe pod -l app.kubernetes.io/name=mongodb

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp

# Delete and redeploy
helm uninstall my-mongo
helm install my-mongo bitnami/mongodb --set auth.enabled=false
```

---

## 📖 Script Dependencies

```
deploy_all.sh
  ├─ Requires: kubectl, helm, docker, minikube
  └─ Calls: setup_monitoring.sh (indirectly via kubectl apply)

setup_monitoring.sh
  ├─ Requires: kubectl
  └─ Deploys: prometheus-config.yaml, grafana.yaml, behavior-dashboard.yaml

monitor_streaming.sh
  ├─ Requires: kubectl
  └─ Calls: view_metrics.sh (option 4)

view_metrics.sh
  ├─ Requires: kubectl, mongosh (in MongoDB pod)
  └─ Standalone
```

---

## 🔧 Environment Variables

Scripts respect these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `BROWSER` | Browser command to open URLs | System default |
| `KUBECTL_CONTEXT` | Kubernetes context | Current context |
| `MINIKUBE_DRIVER` | Minikube driver | docker |

Example:
```bash
export BROWSER="/usr/bin/firefox"
bash deploy/scripts/deploy_all.sh
```

---

## 📊 Monitoring Stack Architecture

```
┌─────────────────────────────────────────────┐
│         User Browser (localhost)            │
├─────────────────────────────────────────────┤
│ :3000 Grafana   :4040 Spark UI   :9090 Prom│
└────────────┬────────────────────────────────┘
             │ Port-forwards
┌────────────┴────────────────────────────────┐
│         Kubernetes (Minikube)               │
├─────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │Prometheus│←─│  Spark   │  │ MongoDB  │ │
│  │  :9090   │  │  :4040   │  │ Exporter │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │               │       │
│  ┌────┴─────┐  ┌───┴────┐  ┌──────┴────┐ │
│  │ Grafana  │  │ Spark  │  │  MongoDB  │ │
│  │  :3000   │  │Streaming│  │  :27017   │ │
│  └──────────┘  └────────┘  └───────────┘ │
└─────────────────────────────────────────────┘
```

---

## ✅ Health Checks

Quick health check command:
```bash
kubectl get pods | grep -E "spark|prometheus|grafana|mongodb" && \
curl -s http://localhost:9090/-/healthy && \
curl -s http://localhost:3000/api/health
```

Expected output:
```
spark-streaming-xxx          1/1     Running
prometheus-xxx               1/1     Running
grafana-xxx                  1/1     Running
mongodb-exporter-xxx         1/1     Running
Prometheus is Healthy.
{"commit":"...","database":"ok","version":"..."}
```

---

## 🎓 Best Practices

1. **Always use `deploy_all.sh` for initial setup**
   - Handles all dependencies and prerequisites
   - Sets up monitoring automatically

2. **Use `monitor_streaming.sh` for development**
   - Interactive menu is easier than remembering commands
   - Quick access to logs and metrics

3. **Use `view_metrics.sh` for automated checks**
   - Great for CI/CD pipelines
   - No UI dependencies

4. **Keep port-forwards running**
   - Don't kill them unless necessary
   - They auto-reconnect on pod restarts

5. **Check logs when things go wrong**
   - Spark: `kubectl logs deployment/spark-streaming-advanced`
   - MongoDB: `kubectl logs -l app.kubernetes.io/name=mongodb`
   - Kafka: `kubectl logs -l strimzi.io/name=my-cluster-kafka`

---

## 📚 Related Documentation

- [Monitoring Stack README](../kubernetes/monitoring/README.md)
- [Spark Deployments](../kubernetes/base/spark-deployments.yaml)
- [Kafka Configuration](../kubernetes/base/kafka-strimzi.yaml)
- [Main README](/README.md)

---

**Last Updated:** December 1, 2025
