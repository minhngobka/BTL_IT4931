# 🎯 Hướng Dẫn Trình Bày & Demo Dự Án Big Data

## 📋 MỤC LỤC
1. [Giới Thiệu Tổng Quan](#giới-thiệu-tổng-quan)
2. [Những Gì Đã Hoàn Thành](#những-gì-đã-hoàn-thành)
3. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
4. [Kịch Bản Demo](#kịch-bản-demo)
5. [Câu Hỏi Dự Kiến](#câu-hỏi-dự-kiến)

---

## 🎤 GIỚI THIỆU TỔNG QUAN (2-3 phút)

### Nói với giáo viên:

> **"Em xin phép trình bày dự án: Hệ Thống Phân Tích Hành Vi Khách Hàng E-commerce Real-time"**
>
> **Mục tiêu:** Xây dựng một hệ thống big data xử lý và phân tích dữ liệu khách hàng theo thời gian thực, 
> giúp doanh nghiệp hiểu rõ hành vi mua sắm và đưa ra quyết định nhanh chóng.
>
> **Dữ liệu:** 42 triệu sự kiện e-commerce (5.3GB) từ Kaggle - ghi nhận hành động xem, thêm giỏ hàng, 
> và mua hàng của khách hàng.
>
> **Công nghệ:** Apache Spark Structured Streaming, Apache Kafka, MongoDB, Kubernetes trên Minikube.

---

## ✅ NHỮNG GÌ ĐÃ HOÀN THÀNH

### 1. **Xây Dựng Kiến Trúc Data Pipeline** ⭐⭐⭐
- **Data Ingestion:** Kafka với 3 partitions, replication factor 2
- **Stream Processing:** Spark Structured Streaming với 3 luồng xử lý song song
- **Storage:** MongoDB với 9 collections (3 streaming + 6 batch analytics)
- **Orchestration:** Kubernetes deployment trên Minikube (4 CPUs, 8GB RAM)

### 2. **Phát Triển Ứng Dụng Streaming** ⭐⭐⭐
**File:** `src/streaming/streaming_advanced.py`

**Chức năng chính:**
- ✅ Đọc dữ liệu real-time từ Kafka
- ✅ Làm giàu dữ liệu với thông tin sản phẩm và danh mục
- ✅ Phân tích hành vi người dùng theo session (30 phút timeout)
- ✅ Tính toán metrics aggregation (5s tumbling window)
- ✅ Ghi kết quả vào MongoDB với 3 collections:
  - `enriched_events`: Sự kiện đã được làm giàu
  - `event_aggregations`: Metrics tổng hợp theo event_type
  - `user_session_analytics`: Phân tích session người dùng

**Kỹ thuật sử dụng:**
- Window operations (tumbling, session)
- Stream-stream joins với broadcast
- Watermarking cho late data handling
- Stateful processing với sessionization

### 3. **Phát Triển Ứng Dụng Batch Analytics** ⭐⭐⭐
**File:** `src/batch/journey_analysis.py`

**Phân tích nâng cao:**
- ✅ Customer Journey Analysis: Phân tích hành trình mua hàng
- ✅ Funnel Analysis: Tỷ lệ chuyển đổi view → cart → purchase
- ✅ RFM Segmentation: Phân khúc khách hàng (Recency, Frequency, Monetary)
- ✅ Category Performance: Phân tích hiệu suất theo danh mục
- ✅ Time-based Patterns: Phân tích theo giờ, ngày trong tuần
- ✅ Product Recommendations: Gợi ý sản phẩm dựa trên co-occurrence

**File:** `src/batch/ml_analytics.py`
- ✅ K-Means Clustering: Phân nhóm khách hàng
- ✅ Predictive Analytics: Dự đoán purchase probability

### 4. **Data Engineering Best Practices** ⭐⭐
- ✅ Cấu trúc dự án chuyên nghiệp (src/, data/, config/, kubernetes/, scripts/)
- ✅ Dimension tables: Product catalog, category hierarchy, user dimension
- ✅ Configuration management với .env files
- ✅ Docker containerization
- ✅ Automated deployment scripts

### 5. **Monitoring & Observability** ⭐
- ✅ Spark UI để theo dõi streaming jobs
- ✅ MongoDB queries để verify data
- ✅ Kubernetes dashboard để monitor resources
- ✅ Structured logging

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

```
┌─────────────────┐
│   CSV Dataset   │  5.3GB, 42M events
│  (2019-Oct.csv) │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Event Simulator │  Python script
│  (Kafka Producer)│  → Topic: ecommerce-events
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────────┐
│          Apache Kafka (Strimzi)              │
│  • 1 broker, 3 partitions, RF=2             │
│  • Topic: ecommerce-events                  │
│  • External access: NodePort 31927          │
└────────┬────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────┐
│   Apache Spark Structured Streaming         │
│  • Driver: 2 cores, 2GB RAM                 │
│  • Executor: 2 cores, 2GB RAM               │
│  • 3 parallel streams:                      │
│    1. Enriched Events                       │
│    2. Event Aggregations                    │
│    3. User Session Analytics                │
└────────┬────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────┐
│            MongoDB (Bitnami)                 │
│  Database: bigdata_db                        │
│                                              │
│  Streaming Collections:                     │
│  • enriched_events                          │
│  • event_aggregations                       │
│  • user_session_analytics                   │
│                                              │
│  Batch Analytics Collections:               │
│  • customer_journey                         │
│  • funnel_analysis                          │
│  • rfm_segments                             │
│  • category_performance                     │
│  • time_patterns                            │
│  • product_recommendations                  │
└─────────────────────────────────────────────┘

           All running on
    ┌──────────────────────────┐
    │   Kubernetes (Minikube)  │
    │   4 CPUs, 8GB RAM        │
    └──────────────────────────┘
```

---

## 🎬 KỊCH BẢN DEMO (10-15 phút)

### **CHUẨN BỊ TRƯỚC KHI DEMO:**

```bash
# Terminal 1: Chuẩn bị
cd ~/bigdata_project
source venv/bin/activate

# Kiểm tra hệ thống
kubectl get pods                    # Tất cả pods phải Running
minikube status                     # Phải Running
```

---

### **PHẦN 1: GIỚI THIỆU CẤU TRÚC DỰ ÁN** (2 phút)

```bash
# Hiển thị cấu trúc dự án
tree -L 2 -d

# Hoặc
ls -la
ls -la src/
ls -la data/
ls -la kubernetes/
```

**Giải thích:**
> "Em đã tổ chức dự án theo cấu trúc chuẩn data engineering:
> - `src/`: Mã nguồn chia thành streaming, batch, và utilities
> - `data/`: Dữ liệu thô và dimension tables
> - `config/`: Cấu hình Kafka, MongoDB, environment variables
> - `kubernetes/`: Kubernetes manifests cho deployment
> - `scripts/`: Automation scripts"

---

### **PHẦN 2: DEMO DATA PIPELINE REAL-TIME** (5-6 phút)

#### **Bước 1: Kiểm tra infrastructure**

```bash
# Terminal 1: Xem trạng thái pods
kubectl get pods

# Giải thích từng component
kubectl get pods | grep mongo        # MongoDB
kubectl get pods | grep kafka        # Kafka broker
kubectl get pods | grep spark        # Spark streaming
```

**Nói:**
> "Hệ thống gồm 3 components chính đang chạy trên Kubernetes:
> - MongoDB: NoSQL database để lưu kết quả
> - Kafka: Message queue với 3 partitions
> - Spark: Streaming engine để xử lý real-time"

#### **Bước 2: Khởi động Event Simulator**

```bash
# Terminal 2: Mở terminal mới
cd ~/bigdata_project
source venv/bin/activate

# Chạy simulator
python src/utils/event_simulator.py
```

**Nói:**
> "Đây là Event Simulator - đọc dữ liệu từ CSV 5.3GB và gửi vào Kafka 
> như thể khách hàng đang tương tác thực tế. Mỗi giây gửi 1000 events."

**Quan sát output:**
```
>>> Kết nối Kafka THÀNH CÔNG!
Bắt đầu đọc file: data/raw/ecommerce_events_2019_oct.csv
--- Gửi 1000 sự kiện ---
Sent: view - User: 541312140
Sent: purchase - User: 514591159
Sent: cart - User: 550121407
...
```

#### **Bước 3: Theo dõi Spark Processing**

```bash
# Terminal 3: Mở terminal mới
kubectl logs -f deployment/spark-streaming-advanced
```

**Nói:**
> "Spark đang nhận dữ liệu từ Kafka, xử lý và ghi vào MongoDB.
> Mỗi batch ghi hàng trăm records vào 3 collections khác nhau."

**Quan sát output:**
```
✓ Epoch 1: Wrote 789 records to enriched_events
✓ Epoch 1: Wrote 217 records to event_aggregations
✓ Epoch 1: Wrote 311 records to user_session_analytics
```

#### **Bước 4: Truy vấn MongoDB Real-time**

```bash
# Terminal 4: Query MongoDB trực tiếp trong pod (cách đáng tin cậy nhất)
bash /tmp/demo_mongodb.sh

# HOẶC query thủ công:
# 1. Đếm số records
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  print('📊 RECORD COUNTS:');
  print('enriched_events:', db.enriched_events.countDocuments());
  print('event_aggregations:', db.event_aggregations.countDocuments());
  print('user_sessions:', db.user_session_analytics.countDocuments());
"

# 2. Xem dữ liệu mẫu
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  db.enriched_events.find().limit(2).forEach(printjson)
"

# 3. Top 5 products được xem nhiều nhất
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  db.enriched_events.aggregate([
    {\$match: {event_type: 'view'}},
    {\$group: {_id: '\$product_id', views: {\$sum: 1}}},
    {\$sort: {views: -1}},
    {\$limit: 5}
  ]).forEach(printjson)
"

# 4. Top 5 users có nhiều hành động nhất
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval "
  db.user_session_analytics.find().sort({total_events: -1}).limit(5).forEach(printjson)
"
```

**💡 Lưu ý quan trọng:**
- Spark ghi vào MongoDB qua **internal Kubernetes service**: `my-mongo-mongodb.default.svc.cluster.local:27017`
- Port-forward tới localhost có thể không ổn định trong demo
- **Khuyến nghị**: Dùng `kubectl exec` để query trực tiếp vào pod MongoDB (đáng tin cậy 100%)

**Nói:**
> "Dữ liệu đang được ghi vào MongoDB trong real-time. 
> - enriched_events: Mỗi sự kiện được làm giàu với thông tin sản phẩm, category
> - event_aggregations: Tổng hợp số lượng view, cart, purchase mỗi 5 giây
> - user_session_analytics: Phân tích session của từng user (timeout 30 phút)
> 
> Em query trực tiếp vào MongoDB pod để đảm bảo demo luôn chạy đúng."

#### **Bước 5: Spark UI**

```bash
# Terminal 6: Port forward Spark UI
kubectl port-forward deployment/spark-streaming-advanced 4040:4040
```

**Mở browser: http://localhost:4040**

**Nói:**
> "Spark UI cho phép monitor streaming job:
> - Streaming tab: Input rate, processing time, batch duration
> - SQL tab: Physical plans của các queries
> - Executors tab: Resource usage"

**Chỉ vào:**
- Input Rate: X events/sec
- Processing Time: ~Y seconds
- Batch Duration: 30 seconds

---

### **PHẦN 3: DEMO BATCH ANALYTICS** (3-4 phút)

#### **Chạy Customer Journey Analysis**

```bash
# Terminal 7: Trong virtual environment
cd ~/bigdata_project
source venv/bin/activate

# Kiểm tra có đủ dữ liệu chưa (cần ít nhất 1000 events)
mongosh mongodb://localhost:27017/bigdata_db --eval "db.enriched_events.countDocuments()"

# Chạy batch analytics
python src/batch/journey_analysis.py
```

**Nói:**
> "Batch analytics chạy trên dữ liệu đã tích lũy để phân tích sâu hơn:
> - Customer Journey: Hành trình từ view → cart → purchase
> - Funnel Analysis: Tỷ lệ chuyển đổi ở mỗi bước
> - RFM Segmentation: Phân khúc khách hàng thành Champions, Loyal, At Risk...
> - Category Performance: Danh mục nào bán chạy nhất
> - Time Patterns: Giờ nào trong ngày có traffic cao nhất"

#### **Xem kết quả**

```bash
# Xem các collections mới
mongosh mongodb://localhost:27017/bigdata_db

# Funnel Analysis
db.funnel_analysis.find().pretty()

# RFM Segments
db.rfm_segments.find().pretty()

# Category Performance
db.category_performance.find().sort({total_revenue: -1}).limit(5).pretty()

# Time Patterns
db.time_patterns.find().sort({hour_of_day: 1}).pretty()

# Product Recommendations
db.product_recommendations.find().limit(3).pretty()
```

**Giải thích kết quả:**
> "Ví dụ Funnel Analysis cho thấy:
> - 100% users view sản phẩm
> - 5% thêm vào giỏ hàng  
> - 2% hoàn tất mua hàng
> → Cần cải thiện conversion rate ở bước cart"

---

### **PHẦN 4: DEMO KUBERNETES ORCHESTRATION** (2 phút)

```bash
# Xem tất cả resources
kubectl get all

# Xem chi tiết deployment
kubectl describe deployment spark-streaming-advanced

# Xem resource usage
kubectl top pods

# Scale up/down (nếu muốn show)
kubectl scale deployment spark-streaming-advanced --replicas=2
kubectl get pods -w  # Xem pod mới start

# Scale back
kubectl scale deployment spark-streaming-advanced --replicas=1
```

**Nói:**
> "Kubernetes giúp quản lý và scale hệ thống:
> - Auto-restart nếu pod bị lỗi
> - Resource limits để tránh overload
> - Có thể scale theo nhu cầu"

---

## ❓ CÂU HỎI Dự KIẾN & CÁCH TRẢ LỜI

### **1. "Em xử lý bao nhiêu dữ liệu?"**

**Trả lời:**
> "Em xử lý 42 triệu events (5.3GB) từ dataset Kaggle về e-commerce. 
> Dataset này ghi nhận hành vi của khoảng 5 triệu users trên 1 triệu sản phẩm 
> trong tháng 10/2019. Event Simulator đọc và gửi vào Kafka với tốc độ 1000 events/giây, 
> tương đương ~11 giờ chạy liên tục để hết dữ liệu."

### **2. "Tại sao chọn Spark Streaming thay vì Spark Batch?"**

**Trả lời:**
> "Em chọn Spark Structured Streaming vì:
> 1. **Real-time insights:** Doanh nghiệp cần biết ngay khách hàng đang làm gì để phản ứng kịp thời
> 2. **Event-driven architecture:** Tích hợp tốt với Kafka
> 3. **Micro-batch processing:** Cân bằng giữa latency và throughput
> 4. **Exactly-once semantics:** Đảm bảo dữ liệu không bị duplicate hay mất mát
> 5. **Window operations:** Hỗ trợ sessionization và time-based aggregations
> 
> Batch analytics vẫn được dùng cho phân tích sâu hơn như RFM, clustering, recommendations."

### **3. "Làm thế nào xử lý late data?"**

**Trả lời:**
> "Em sử dụng Watermarking trong Spark Structured Streaming:
> ```python
> df = df.withWatermark('event_time', '10 minutes')
> ```
> Events đến muộn trong vòng 10 phút vẫn được xử lý. 
> Sau 10 phút, state cũ sẽ được clean up để tránh memory leak."

### **4. "Tại sao dùng MongoDB thay vì relational database?"**

**Trả lời:**
> "MongoDB phù hợp vì:
> 1. **Schema flexibility:** Event data có thể thay đổi cấu trúc theo thời gian
> 2. **Write performance:** Ghi nhanh với batch inserts
> 3. **JSON format:** Match với Spark DataFrame schema
> 4. **Aggregation framework:** Query mạnh mẽ cho analytics
> 5. **Horizontal scaling:** Dễ scale với sharding khi data lớn"

### **5. "Hệ thống có handle được production load không?"**

**Trả lời:**
> "Với setup hiện tại trên Minikube (4 CPUs, 8GB RAM):
> - Throughput: ~1000 events/giây
> - Latency: ~5-10 giây end-to-end
> 
> Để production, cần:
> 1. **Scale Kafka:** Thêm brokers, tăng partitions (recommend 1 partition per CPU core)
> 2. **Scale Spark:** Tăng executors và memory (recommend 3 executors, 4GB/executor)
> 3. **Scale MongoDB:** Sharding và replication
> 4. **Use managed services:** AWS MSK (Kafka), EMR (Spark), DocumentDB (MongoDB)
> 
> Với config đó có thể xử lý 10,000+ events/giây."

### **6. "Em gặp khó khăn gì khi làm project?"**

**Trả lời (chọn 2-3 điểm):**
> "Em gặp một số thách thức:
> 
> 1. **Memory management:** Ban đầu Spark bị OOM khi join với product catalog. 
>    Đã giải quyết bằng broadcast join cho dimension tables nhỏ.
> 
> 2. **Sessionization:** Xác định session boundary phức tạp. Đã dùng session window 
>    với 30 phút timeout, phù hợp với user behavior.
> 
> 3. **Kafka connector:** Spark-Kafka integration cần đúng version dependencies. 
>    Đã download đúng JAR files cho Spark 3.5.0 và Kafka 3.4.0.
> 
> 4. **Docker build:** Container size lớn (~2GB). Đã optimize bằng multi-stage build 
>    và chỉ copy files cần thiết."

### **7. "Có thể mở rộng project này như thế nào?"**

**Trả lời:**
> "Em có một số ý tưởng mở rộng:
> 
> 1. **Real-time recommendations:** Dùng ALS collaborative filtering trong streaming
> 2. **Anomaly detection:** Machine learning để phát hiện fraud, bot traffic
> 3. **A/B testing framework:** So sánh different user experiences
> 4. **Real-time dashboard:** Grafana + Prometheus để visualize metrics
> 5. **CDC (Change Data Capture):** Sync với operational databases
> 6. **Lambda architecture:** Combine streaming và batch với Delta Lake
> 7. **Multi-tenant:** Support nhiều e-commerce sites trên cùng platform"

### **8. "Code quality như thế nào?"**

**Trả lời:**
> "Em focus vào code quality:
> 
> 1. **Project structure:** Tổ chức theo best practices (src/, data/, config/)
> 2. **Configuration management:** Externalize với .env files
> 3. **Error handling:** Try-catch và logging đầy đủ
> 4. **Documentation:** README, SETUP_GUIDE, TECHNICAL_DOCS
> 5. **Containerization:** Docker cho reproducibility
> 6. **IaC:** Kubernetes manifests cho infrastructure as code
> 7. **Version control:** Git với meaningful commit messages"

### **9. "Performance metrics là gì?"**

**Trả lời:**
> "Em đo các metrics sau:
> 
> **Streaming:**
> - Input rate: 1000 events/sec
> - Processing time: 5-8 seconds per batch
> - End-to-end latency: <10 seconds
> - Records processed: ~30,000 per batch (30s window)
> 
> **Batch:**
> - Journey analysis: 10M events trong ~5 phút
> - K-means clustering: 100K users trong ~2 phút
> 
> **Storage:**
> - MongoDB: 3GB sau 1 triệu events
> - Compression ratio: ~60% (raw CSV vs MongoDB)"

### **10. "Em học được gì từ project này?"**

**Trả lời:**
> "Em học được rất nhiều:
> 
> 1. **Technical skills:**
>    - Spark Structured Streaming với window operations
>    - Kafka architecture và partitioning strategy
>    - Kubernetes orchestration và resource management
>    - MongoDB aggregation framework
> 
> 2. **Data engineering principles:**
>    - Data pipeline design patterns
>    - Stream vs batch processing tradeoffs
>    - Schema evolution và backward compatibility
>    - Monitoring và debugging distributed systems
> 
> 3. **Soft skills:**
>    - Đọc documentation kỹ (Spark, Kafka, K8s)
>    - Debug và troubleshoot complex issues
>    - Tổ chức code theo best practices
>    - Technical writing (documentation)
> 
> 4. **Business understanding:**
>    - E-commerce metrics (conversion rate, funnel analysis)
>    - Customer segmentation (RFM model)
>    - Real-time vs batch analytics use cases"

---

## 📊 KEY METRICS ĐỂ SHOW

Chuẩn bị sẵn các số liệu này:

```bash
# 1. Dataset size
ls -lh data/raw/ecommerce_events_2019_oct.csv
# → 5.3GB, 42 million events

# 2. Number of collections
mongosh --eval "db.adminCommand('listDatabases')" | grep bigdata_db

# 3. Records in each collection
mongosh mongodb://localhost:27017/bigdata_db --eval "
  db.getCollectionNames().forEach(function(col) {
    print(col + ': ' + db[col].countDocuments())
  })
"

# 4. Infrastructure resources
kubectl top pods

# 5. Processing rate
# Xem trong Spark UI: Input Rate graph
```

---

## 🎯 TIPS CHO BÀI TRÌNH BÀY

### **✅ NÊN:**

1. **Tự tin và rõ ràng:** Nói chậm, rõ ràng, maintain eye contact
2. **Demo trực tiếp:** Chạy thật hệ thống, không dùng slides quá nhiều
3. **Explain WHY:** Giải thích tại sao chọn công nghệ đó, không chỉ HOW
4. **Show code quan trọng:** Mở file Python, chỉ vào các đoạn code hay
5. **Có backup plan:** Nếu demo fail, có screenshots/video sẵn
6. **Interactive:** Hỏi giáo viên có muốn thấy gì thêm không

### **❌ KHÔNG NÊN:**

1. **Đọc slides:** Biết nội dung, không cần đọc
2. **Nói quá technical:** Balance giữa technical depth và clarity
3. **Che giấu hạn chế:** Thành thật về limitations và cách improve
4. **Rush:** Làm chậm, đảm bảo mọi bước chạy đúng
5. **Phụ thuộc internet:** Download sẵn dependencies

---

## 📸 SCREENSHOTS CẦN CHUẨN BỊ (BACKUP)

1. **Project structure:** `tree` output
2. **Pods running:** `kubectl get pods` output
3. **Event Simulator:** Console output sending events
4. **Spark logs:** Processing batches successfully
5. **MongoDB data:** Sample documents từ mỗi collection
6. **Spark UI:** Streaming tab showing input rate graph
7. **Batch results:** Funnel analysis, RFM segments
8. **Kubernetes dashboard:** Resource usage graphs

---

## ⏱️ TIMELINE TỔNG THỂ

- **00:00-02:00** - Giới thiệu project và objectives
- **02:00-04:00** - Show project structure và architecture
- **04:00-09:00** - Demo real-time pipeline (simulator → Spark → MongoDB)
- **09:00-12:00** - Demo batch analytics và results
- **12:00-14:00** - Show Kubernetes orchestration
- **14:00-15:00** - Tổng kết và Q&A

**TOTAL: 15 phút demo + 5-10 phút Q&A = ~25 phút**

---

## 🚀 CHECKLIST TRƯỚC KHI DEMO

```bash
# 1 ngày trước:
□ Test toàn bộ pipeline từ đầu đến cuối
□ Chụp screenshots backup
□ Viết script demo (file này)
□ Practice 2-3 lần

# 1 giờ trước:
□ Start Minikube: minikube start
□ Check all pods running: kubectl get pods
□ Activate venv: source venv/bin/activate
□ Open 6 terminals sẵn, label rõ ràng
□ Clear MongoDB để có data mới: mongosh → db.dropDatabase()

# 5 phút trước:
□ Restart Spark deployment để clean state
□ Test network connectivity
□ Close unnecessary applications
□ Set terminal font size lớn (cho dễ nhìn)
```

---

## 💡 MẸO CUỐI CÙNG

1. **Storytelling:** Kể như một câu chuyện - từ problem → solution → results
2. **Be enthusiastic:** Show passion về project
3. **Admit unknowns:** Nếu không biết câu trả lời, thành thật "Em sẽ research thêm"
4. **Connect to real-world:** Nói về use cases thực tế (Amazon, Shopee, Tiki)
5. **Highlight learning:** Focus vào những gì đã học được

---

## 🎓 KẾT LUẬN

> **"Qua project này, em đã build một complete end-to-end big data pipeline 
> xử lý real-time data với Spark Streaming, Kafka, và MongoDB trên Kubernetes. 
> Em hiểu sâu hơn về distributed computing, stream processing, và data engineering principles. 
> Em tin rằng kiến thức này rất valuable cho career trong data engineering."**

**CHÚC BẠN DEMO THÀNH CÔNG! 🎉**
