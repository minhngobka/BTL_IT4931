# 🎯 DEMO CHEATSHEET - In Ra & Đặt Bên Cạnh

## 📝 GIỚI THIỆU 30 GIÂY

> "Em làm hệ thống Big Data phân tích hành vi khách hàng e-commerce real-time với:
> - 42 triệu events (5.3GB)
> - Spark Streaming + Kafka + MongoDB
> - Chạy trên Kubernetes"

---

## 🔧 CÀI ĐẶT NHANH (5 phút trước demo)

```bash
# Terminal 1 - Main
cd ~/bigdata_project
source venv/bin/activate
kubectl get pods  # Tất cả phải Running
```

---

## 🎬 DEMO SCRIPT (10 phút)

### 1️⃣ SHOW PROJECT (1 phút)
```bash
tree -L 2
ls -lh data/raw/ecommerce_events_2019_oct.csv  # 5.3GB
```

### 2️⃣ START PIPELINE (2 phút)
```bash
# Terminal 2
python src/utils/event_simulator.py
# Chờ thấy: "Sent: view - User: 541312140"
```

### 3️⃣ WATCH SPARK (2 phút)
```bash
# Terminal 3
kubectl logs -f deployment/spark-streaming-advanced
# Chờ thấy: "✓ Epoch X: Wrote XXX records"
```

### 4️⃣ QUERY MONGODB (3 phút)
```bash
# Terminal 4 - Cách NHANH và ĐÁNG TIN CẬY nhất
bash /tmp/demo_mongodb.sh

# HOẶC query thủ công:
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  print('📊 Records:', db.enriched_events.countDocuments());
  db.enriched_events.find().limit(2).forEach(printjson);
"

# Top 5 products
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  db.enriched_events.aggregate([
    {\$match: {event_type: 'view'}},
    {\$group: {_id: '\$product_id', views: {\$sum: 1}}},
    {\$sort: {views: -1}},
    {\$limit: 5}
  ]).forEach(printjson)
"
```

**💡 TIP:** Dùng `kubectl exec` thay vì port-forward để demo luôn chạy đúng!

### 5️⃣ BATCH ANALYTICS (2 phút)
```bash
# Terminal 5
python src/batch/journey_analysis.py

# Xem kết quả
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  db.funnel_analysis.find().forEach(printjson);
  db.rfm_segments.find().forEach(printjson);
"
```

---

## 💬 10 CÂU HỎI THƯỜNG GẶP

### 1. "Xử lý bao nhiêu dữ liệu?"
→ **42 triệu events (5.3GB), đã xử lý 173K+ events real-time với tốc độ 1000 events/giây**

### 2. "Tại sao dùng Spark Streaming?"
→ **Real-time insights, exactly-once semantics, window operations**

### 3. "Xử lý late data thế nào?"
→ **Watermarking 10 phút**

### 4. "Tại sao MongoDB?"
→ **Schema flexible, write nhanh, aggregation mạnh**

### 5. "Production throughput?"
→ **Hiện tại: 1K events/s (đã test thành công). Scale lên: 10K+ events/s**

### 6. "Khó khăn gặp phải?"
→ **Memory OOM → Broadcast join. Kafka version mismatch → Download đúng JAR. Port-forward không ổn định → kubectl exec**

### 7. "Mở rộng như nào?"
→ **Real-time recommendations, anomaly detection, A/B testing**

### 8. "Code quality?"
→ **Project structure chuẩn, config externalized, Docker, K8s IaC**

### 9. "Performance metrics?"
→ **Latency <10s, throughput 1K/s, 173K+ records đã xử lý**

### 10. "Học được gì?"
→ **Spark streaming, Kafka architecture, K8s orchestration, data pipeline design, troubleshooting distributed systems**

---

## 📊 KEY NUMBERS (SỐ LIỆU THỰC TẾ)

| Metric | Value |
|--------|-------|
| Dataset | 5.3GB, 42M events |
| **Đã xử lý** | **173,707 events** |
| Users | ~5 million |
| Products | ~1 million |
| **Top Product** | **ID 1004856: 1,838 views** |
| **Top User** | **ID 550284046: 4,300 events** |
| Input Rate | 1000 events/sec |
| Latency | <10 seconds |
| Collections | 9 (3 streaming + 6 batch) |
| Kafka Partitions | 3 |
| Spark Resources | 2 cores, 2GB RAM |

---

## 🆘 TROUBLESHOOTING

### Pod không Running?
```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Simulator không connect được Kafka?
```bash
# Check Kafka service
kubectl get svc | grep kafka

# Update config
export MINIKUBE_IP=$(minikube ip)
sed -i "s|KAFKA_EXTERNAL_BROKER=.*|KAFKA_EXTERNAL_BROKER=$MINIKUBE_IP:31927|" config/.env
```

### MongoDB không có data?
```bash
# Check Spark logs
kubectl logs deployment/spark-streaming-advanced --tail=30

# Query trực tiếp vào pod (không dùng port-forward)
bash scripts/demo_mongodb.sh

# Restart Spark nếu cần
kubectl rollout restart deployment/spark-streaming-advanced
```

---

## ✅ CHECKLIST

**30 phút trước:**
- [ ] Minikube running
- [ ] All pods Running
- [ ] Clear MongoDB (optional)
- [ ] 6 terminals ready
- [ ] Font size lớn

**5 phút trước:**
- [ ] Test simulator
- [ ] Test MongoDB connect
- [ ] Close apps không cần
- [ ] Đọc lại script 1 lần

**Trong khi demo:**
- [ ] Nói chậm, rõ ràng
- [ ] Giải thích tại sao (why), không chỉ làm thế nào (how)
- [ ] Show code quan trọng
- [ ] Tự tin!

---

## 🎯 KẾT LUẬN 30 GIÂY

> "Em đã xây dựng complete pipeline xử lý 42M events real-time với Spark, Kafka, MongoDB trên K8s. 
> System có thể scale, monitor được, và apply nhiều use cases thực tế. 
> Em học được distributed computing, stream processing, và data engineering best practices."

---

**GHI NHỚ:** Breathe, smile, be confident! 🚀
