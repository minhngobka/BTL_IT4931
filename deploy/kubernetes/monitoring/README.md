# 📊 Monitoring Stack - User Behavior Classification

Complete monitoring solution with **Spark UI**, **Prometheus**, and **Grafana** for real-time behavior classification pipeline.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Kafka Events → Spark Streaming → MongoDB                  │
│                      ↓                                      │
│              ┌──────────────┐                               │
│              │  Prometheus  │ ← Spark Metrics (JMX)        │
│              │   :9090      │ ← MongoDB Exporter           │
│              └──────┬───────┘                               │
│                     ↓                                       │
│              ┌──────────────┐                               │
│              │   Grafana    │ ← Dashboards                 │
│              │   :3000      │ ← Alerts                     │
│              └──────────────┘                               │
│                                                             │
│              ┌──────────────┐                               │
│              │   Spark UI   │ ← Job Details                │
│              │   :4040      │ ← DAG Visualization          │
│              └──────────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Deploy Monitoring Stack

```bash
# One-command setup
bash deploy/scripts/setup_monitoring.sh
```

This will:
- ✅ Deploy Prometheus
- ✅ Deploy Grafana with pre-configured dashboards
- ✅ Expose Spark UI
- ✅ Setup MongoDB exporter
- ✅ Start port-forwards to localhost

### 2. Access Dashboards

After deployment completes:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin123 |
| **Spark UI** | http://localhost:4040 | - |
| **Prometheus** | http://localhost:9090 | - |

---

## 📈 Grafana Dashboards

### **User Behavior Classification Dashboard**

Pre-configured dashboard with:

#### 📊 **Overview Panels**
- Total sessions classified
- Average session duration
- Total revenue
- Processing rate (events/sec)

#### 🎯 **Segment Analysis**
- **Pie Chart**: Segment distribution
  - 🔴 Bouncer
  - 🟡 Browser
  - 🟢 Engaged Shopper
  - 🔵 Power User

- **Time Series**: Sessions per minute by segment
- **Bar Gauge**: Conversion rates by segment

#### 💰 **Revenue Metrics**
- Revenue by segment
- Average order value
- Top 10 power users

#### ⚡ **Performance Metrics**
- Spark streaming processing rate
- End-to-end latency
- Kafka lag
- MongoDB write throughput

#### 🔥 **Heatmaps**
- Session duration distribution
- Events per session distribution
- Time-of-day patterns

---

## 🎯 Spark UI Usage

### Access Spark UI

```bash
# Option 1: Via setup script (auto port-forward)
bash deploy/scripts/setup_monitoring.sh

# Option 2: Manual port-forward
kubectl port-forward svc/spark-streaming-svc 4040:4040
```

### Key Tabs in Spark UI

#### 1. **Streaming Tab**
- Input Rate: Events/sec from Kafka
- Processing Time: Batch processing duration
- Scheduling Delay: Queue time before processing
- Total Delay: End-to-end latency

**What to monitor:**
```
✅ Input Rate: Should be steady
✅ Processing Time < Batch Interval (500ms)
⚠️  Scheduling Delay > 0: Processing backlog
❌ Total Delay increasing: System overloaded
```

#### 2. **SQL Tab**
- View DataFrame transformations
- Check join strategies (broadcast vs shuffle)
- Identify slow operations

#### 3. **Executors Tab**
- Memory usage
- Task distribution
- GC time (should be < 10%)

#### 4. **Streaming Statistics**
```
Batch Duration: 500ms target
Records/batch: ~1000-5000 optimal
Watermark: 10 minutes (late data tolerance)
```

---

## 📊 Prometheus Queries

### Custom Metrics Available

#### Session Metrics
```promql
# Total sessions classified
spark_streaming_sessions_total

# Sessions by segment (last 5 min)
rate(spark_streaming_sessions_by_segment[5m])

# Current segment distribution
spark_streaming_segment_distribution
```

#### Performance Metrics
```promql
# Processing rate (records/sec)
rate(spark_streaming_records_processed[1m])

# Current latency
spark_streaming_processing_latency_ms

# Session duration percentiles
histogram_quantile(0.95, spark_streaming_session_duration_minutes)

# Events per session p99
histogram_quantile(0.99, spark_streaming_events_per_session)
```

#### MongoDB Metrics
```promql
# Documents inserted/sec
rate(mongodb_op_counters_total{type="insert"}[1m])

# Query latency
mongodb_op_latencies_histogram{type="command"}

# Connection pool usage
mongodb_connections{state="current"}
```

---

## 🔍 Interactive Monitoring

### Real-time CLI Monitor

```bash
bash deploy/scripts/monitor_streaming.sh
```

**Features:**
1. View Spark application logs
2. Check streaming query status
3. Query MongoDB collections
4. Live segment distribution
5. Quick access to Spark UI
6. Quick access to Grafana
7. View Prometheus metrics
8. Tail logs in real-time

### Quick Metrics View (No UI)

```bash
bash deploy/scripts/view_metrics.sh
```

**Output:**
```
📊 User Behavior Classification Metrics
========================================

🎯 Segment Distribution:
========================
bouncer              1250 sessions █████████████
browser               850 sessions █████████
engaged_shopper       450 sessions █████
power_user            150 sessions ██

💰 Revenue by Segment:
======================
power_user           $15,234.50
engaged_shopper      $8,450.25
browser              $1,200.00
bouncer              $0.00

📈 Conversion Funnel:
====================
bouncer
  View → Cart:     0.00%
  Cart → Purchase: 0.00%
  Overall:         0.00%

browser
  View → Cart:     35.50%
  Cart → Purchase: 0.00%
  Overall:         0.00%
```

---

## 🚨 Alerting (Optional)

### Configure Grafana Alerts

1. Open Grafana → Alerting → New alert rule

2. **High Processing Latency Alert**
```promql
spark_streaming_processing_latency_ms > 5000
```
**Action:** Check Spark UI for bottlenecks

3. **Low Conversion Rate Alert**
```promql
spark_streaming_conversion_rate{segment="engaged_shopper"} < 0.05
```
**Action:** Review browser segment recommendations

4. **System Overload Alert**
```promql
rate(spark_streaming_sessions_total[1m]) > 1000
```
**Action:** Scale up Spark executors

---

## 🛠️ Troubleshooting

### Issue: Grafana Dashboard Shows No Data

**Check:**
```bash
# 1. Verify Prometheus is scraping
kubectl logs deployment/prometheus | grep -i error

# 2. Check Prometheus targets
kubectl port-forward svc/prometheus 9090:9090
# Visit: http://localhost:9090/targets

# 3. Verify MongoDB exporter
kubectl logs deployment/mongodb-exporter
```

### Issue: Spark UI Not Accessible

**Check:**
```bash
# 1. Verify Spark pod is running
kubectl get pod -l app=spark-streaming

# 2. Check if port 4040 is exposed
kubectl describe pod <spark-pod-name> | grep -A5 Ports

# 3. Test port-forward
kubectl port-forward <spark-pod-name> 4040:4040
curl http://localhost:4040
```

### Issue: High Latency in Spark Streaming

**Diagnosis:**
1. Open Spark UI → Streaming tab
2. Check "Scheduling Delay"
   - **> 0**: Batches queuing up (processing slower than input)
3. Check "Processing Time"
   - **> 500ms**: Optimize transformations

**Solutions:**
```python
# Increase parallelism
.config("spark.sql.shuffle.partitions", "16")  # Default: 8

# Increase batch interval
.trigger(processingTime="1 second")  # Default: 500ms

# Increase resources
resources:
  limits:
    cpu: "4000m"  # Increase from 2000m
    memory: "8Gi"  # Increase from 4Gi
```

### Issue: MongoDB Write Bottleneck

**Check:**
```bash
# Monitor MongoDB metrics
kubectl exec -it <mongo-pod> -- mongosh admin --eval '
  db.serverStatus().opcounters
'

# Check connection pool
db.serverStatus().connections
```

**Optimize:**
```python
# Increase batch size
.option("spark.mongodb.output.batch.size", "1024")  # Default: 512

# Use bulk writes
.option("spark.mongodb.output.ordered", "false")
```

---

## 📚 Best Practices

### 1. **Monitor These Key Metrics**

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Processing Latency | < 1s | 1-5s | > 5s |
| Scheduling Delay | 0ms | < 100ms | > 500ms |
| GC Time | < 10% | 10-20% | > 20% |
| Conversion Rate | > 5% | 2-5% | < 2% |

### 2. **Dashboard Refresh Rates**

- **Real-time (5s)**: Processing rate, latency
- **Medium (30s)**: Segment distribution, conversion rates
- **Low (5m)**: Revenue trends, long-term patterns

### 3. **Resource Tuning**

```yaml
# Spark Streaming (Production)
resources:
  requests:
    cpu: "2000m"
    memory: "4Gi"
  limits:
    cpu: "4000m"
    memory: "8Gi"

# Prometheus
resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "1000m"
    memory: "2Gi"

# Grafana
resources:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "500m"
    memory: "1Gi"
```

---

## 🎓 Advanced Usage

### Custom Grafana Dashboard

1. Create new dashboard in Grafana
2. Add panel with MongoDB data source
3. Use aggregation pipeline:

```javascript
// MongoDB aggregation in Grafana
db.user_behavior_segments.aggregate([
  {
    $match: {
      timestamp: {
        $gte: ISODate("${__from}"),
        $lte: ISODate("${__to}")
      }
    }
  },
  {
    $group: {
      _id: {
        segment: "$behavior_segment",
        hour: {$dateToString: {format: "%Y-%m-%d %H:00", date: "$timestamp"}}
      },
      count: {$sum: 1},
      avg_score: {$avg: "$segment_score"}
    }
  },
  {$sort: {"_id.hour": 1}}
])
```

### Export Metrics to External Systems

```python
# Send metrics to external endpoint
from app.utils.prometheus_metrics import metrics

# In your Spark job
def on_batch_complete(batch_df):
    # Calculate metrics
    segment_counts = batch_df.groupBy("behavior_segment").count().collect()
    
    # Update Prometheus
    for row in segment_counts:
        metrics.segment_distribution.labels(
            segment=row.behavior_segment
        ).set(row.count)
```

---

## 📖 References

- [Spark Streaming Monitoring](https://spark.apache.org/docs/latest/streaming-programming-guide.html#monitoring-applications)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)

---

## ✅ Quick Health Check

```bash
# All-in-one health check
kubectl get pods | grep -E "spark|prometheus|grafana|mongodb-exporter"

# Expected output:
# spark-streaming-xxx          1/1     Running
# prometheus-xxx               1/1     Running
# grafana-xxx                  1/1     Running
# mongodb-exporter-xxx         1/1     Running
```

🎉 **You're all set! Happy monitoring!**
