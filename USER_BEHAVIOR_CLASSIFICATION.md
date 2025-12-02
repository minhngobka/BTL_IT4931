# User Behavior Classification System

## 📊 Overview

Hệ thống phân loại real-time user behavior thành 4 segments dựa trên cách họ tương tác với e-commerce platform:

### Segments

| Segment | Icon | Criteria | Insight |
|---------|------|----------|---------|
| **Bouncer** | 🔴 | 1-2 events, <1 min, no cart/purchase | Landing page không hấp dẫn? Sai target audience? |
| **Browser** | 🟡 | 3-10 events, 1-10 min, cart but no purchase | Thiếu trust? Giá cao? So sánh competitor? |
| **Engaged Shopper** | 🟢 | 10-30 events, 10-30 min, multiple purchases | Target customer lý tưởng - cần nurture |
| **Power User** | 🔵 | 30+ events, 30+ min, VIP behavior | VIP customer - cần loyalty program |

## 🏗️ Architecture

```
Kafka (events)
    ↓
Spark Streaming
    ↓
Session Metrics Calculation
    ↓
Behavior Classification
    ↓
Recommendation Engine
    ↓
MongoDB Collections:
  - user_behavior_segments (main output)
  - segment_distribution (5-min windows)
  - conversion_funnel (by segment)
  - enriched_events (raw data)
```

## 📁 File Structure

```
app/
├── processors/
│   └── behavior_classifier.py       # Classification logic
├── jobs/
│   └── streaming/
│       └── advanced_streaming.py    # Main streaming job (UPDATED)
└── utils/
    └── test_behavior_generator.py   # Test data generator

deploy/
└── scripts/
    └── query_behavior_segments.sh   # Query results
```

## 🚀 Quick Start

### 1. Start Streaming Job

```bash
# Submit Spark streaming job
kubectl exec -it deployment/spark-master -- spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  /opt/spark/work-dir/app/jobs/streaming/advanced_streaming.py
```

### 2. Generate Test Data

```bash
# Port-forward Kafka
kubectl port-forward svc/kafka 9092:9092 &

# Generate test behavior patterns
python3 app/utils/test_behavior_generator.py localhost:9092 ecommerce_events
```

### 3. Query Results

```bash
# View classification results
./deploy/scripts/query_behavior_segments.sh
```

## 📊 Output Examples

### MongoDB Collection: `user_behavior_segments`

```json
{
  "_id": ObjectId("..."),
  "user_id": 123456,
  "user_session": "browser_123456_1733097600",
  "behavior_segment": "browser",
  "segment_color": "🟡",
  "segment_score": 50,
  "session_start": ISODate("2025-12-01T10:00:00Z"),
  "session_end": ISODate("2025-12-01T10:08:30Z"),
  "session_duration_minutes": 8.5,
  "total_events": 7,
  "view_count": 6,
  "cart_count": 1,
  "purchase_count": 0,
  "unique_products": 5,
  "unique_categories": 2,
  "total_amount": null,
  "engagement_rate": 0.82,
  "cart_conversion_rate": 16.67,
  "purchase_conversion_rate": 0.0,
  "overall_conversion_rate": 0.0,
  "recommendations": [
    "Send abandoned cart email within 1 hour",
    "Offer limited-time discount (5-10%)",
    "Show social proof (reviews, ratings)"
  ],
  "action_priority": 2,
  "processing_time": ISODate("2025-12-01T10:09:00Z")
}
```

### MongoDB Collection: `conversion_funnel`

```json
{
  "_id": ObjectId("..."),
  "behavior_segment": "engaged_shopper",
  "total_sessions": 150,
  "unique_users": 142,
  "total_views": 2850,
  "total_carts": 420,
  "total_purchases": 180,
  "avg_session_duration": 18.5,
  "total_revenue": 85432.50,
  "avg_revenue_per_session": 569.55,
  "view_to_cart_rate": 14.74,
  "cart_to_purchase_rate": 42.86,
  "overall_conversion_rate": 6.32,
  "avg_order_value": 474.63,
  "processing_time": ISODate("2025-12-01T10:09:00Z")
}
```

## 🎯 Business Use Cases

### 1. Real-time Personalization

**Bouncer Detection** → Show exit-intent popup với discount code

```javascript
// Khi phát hiện bouncer pattern
if (user.behavior_segment === 'bouncer') {
  showPopup({
    title: "Wait! Get 10% off your first order",
    coupon: "WELCOME10"
  });
}
```

### 2. Abandoned Cart Recovery

**Browser với Cart** → Send email automation

```python
# Query browsers with abandoned carts
browsers = db.user_behavior_segments.find({
    "behavior_segment": "browser",
    "cart_count": {"$gte": 1},
    "processing_time": {"$gte": datetime.now() - timedelta(hours=1)}
})

for user in browsers:
    send_abandoned_cart_email(
        user_id=user['user_id'],
        discount=10,
        urgency="Limited time offer!"
    )
```

### 3. VIP Customer Retention

**Power User** → Activate loyalty benefits

```python
# Identify power users
power_users = db.user_behavior_segments.find({
    "behavior_segment": "power_user",
    "total_amount": {"$gte": 1000}
})

for user in power_users:
    activate_vip_benefits(
        user_id=user['user_id'],
        tier="platinum",
        benefits=["Free shipping", "24/7 support", "Early access"]
    )
```

### 4. Marketing Campaign Optimization

**Segment Distribution Analysis** → Optimize ad spend

```bash
# Query segment trends
db.segment_distribution.aggregate([
  {$match: {window_start: {$gte: new Date(Date.now() - 24*60*60*1000)}}},
  {$group: {
    _id: "$behavior_segment",
    total_sessions: {$sum: "$session_count"},
    total_revenue: {$sum: "$total_revenue"}
  }}
])

# Result:
# - 60% bouncers → Optimize landing page
# - 25% browsers → Improve checkout flow
# - 10% engaged → Nurture with content
# - 5% power users → Retention focus
```

## 📈 Metrics & KPIs

### Session-Level Metrics

- **Total Events**: Number of interactions per session
- **Session Duration**: Time from first to last event (minutes)
- **View Count**: Number of product views
- **Cart Count**: Items added to cart
- **Purchase Count**: Completed purchases
- **Unique Products**: Product diversity
- **Engagement Rate**: Events per minute
- **Conversion Rates**: View→Cart→Purchase

### Segment-Level KPIs

- **Segment Distribution**: % of sessions per segment
- **Average Revenue per Session**: By segment
- **Conversion Funnel**: View→Cart→Purchase rates
- **Customer Lifetime Value**: Projected by segment

## 🔧 Configuration

### Adjust Classification Thresholds

Edit `app/processors/behavior_classifier.py`:

```python
SEGMENTS = {
    "bouncer": {
        "total_events": (1, 2),        # Change thresholds
        "duration_min": (0, 1),
        "score": 25
    },
    # ... other segments
}
```

### Modify Recommendations

```python
recommendations_map = {
    "bouncer": [
        "Your custom recommendation 1",
        "Your custom recommendation 2"
    ],
    # ...
}
```

## 🧪 Testing

### Generate Specific Behavior Pattern

```python
# Generate only power users
from app.utils.test_behavior_generator import generate_power_user_session

events = generate_power_user_session(
    user_id=999,
    session_id="test_power_999",
    base_time=datetime.now()
)

for event in events:
    producer.send('ecommerce_events', value=event)
```

### Verify Classification

```bash
# Check if user was classified correctly
kubectl exec -it deployment/mongodb -- mongosh bigdata --eval '
db.user_behavior_segments.findOne(
  {user_session: "test_power_999"},
  {behavior_segment: 1, segment_score: 1, total_events: 1}
)
'
```

## 📊 Monitoring

### Spark UI

```bash
kubectl port-forward svc/spark-master 8080:8080
# Open http://localhost:8080
```

### MongoDB Queries

```bash
# Real-time segment counts
watch -n 5 'kubectl exec -it deployment/mongodb -- mongosh bigdata --quiet --eval "
db.user_behavior_segments.aggregate([
  {\$group: {_id: \"\$behavior_segment\", count: {\$sum: 1}}},
  {\$sort: {count: -1}}
])"'
```

## 🎓 Next Steps

1. **ML Enhancement**: Train classifier using historical data
2. **A/B Testing**: Test different thresholds and recommendations
3. **Real-time Dashboard**: Build Grafana/Superset dashboard
4. **Alerting**: Set up alerts for anomalies (spike in bouncers)
5. **Integration**: Connect to email/CRM systems

## 📚 References

- [Spark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [MongoDB Spark Connector](https://www.mongodb.com/docs/spark-connector/current/)
- [E-commerce Analytics Best Practices](https://www.optimizely.com/optimization-glossary/conversion-rate-optimization/)
