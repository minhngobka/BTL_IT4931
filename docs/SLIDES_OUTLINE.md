# 📊 SLIDES OUTLINE - Dự Án Big Data Analytics

---

## SLIDE 1: TITLE
```
HỆ THỐNG PHÂN TÍCH HÀNH VI KHÁCH HÀNG 
E-COMMERCE REAL-TIME

Sinh viên: [Tên bạn]
MSSV: [MSSV]
Môn học: Big Data
Giảng viên: [Tên GV]
```

---

## SLIDE 2: VẤN ĐỀ & MỤC TIÊU

**Vấn đề:**
- Doanh nghiệp e-commerce cần hiểu hành vi khách hàng NGAY LẬP TỨC
- Dữ liệu khách hàng lớn (hàng triệu events/ngày)
- Cần phân tích cả real-time và batch

**Mục tiêu:**
- ✅ Xây dựng data pipeline xử lý real-time
- ✅ Phân tích customer journey
- ✅ Tạo insights cho business decisions
- ✅ Apply big data technologies

---

## SLIDE 3: DATASET

**Nguồn:** Kaggle - E-commerce Behavior Data

| Thông số | Giá trị |
|----------|---------|
| Kích thước | 5.3 GB |
| Số events | 42 triệu |
| Số users | ~5 triệu |
| Số products | ~1 triệu |
| Thời gian | Tháng 10/2019 |
| Event types | view, cart, purchase |

**Cột dữ liệu:**
- event_time, event_type, product_id, category_id
- category_code, brand, price, user_id, user_session

---

## SLIDE 4: KIẾN TRÚC HỆ THỐNG

```
┌───────────────┐
│  CSV Dataset  │ 5.3GB
└───────┬───────┘
        │
        ↓
┌───────────────┐
│ Event Simulator│ Kafka Producer
└───────┬───────┘
        │
        ↓
┌───────────────┐
│  Kafka Broker │ 3 partitions
└───────┬───────┘
        │
        ↓
┌───────────────────────────┐
│ Spark Streaming           │
│ • Enrichment              │
│ • Aggregation             │
│ • Sessionization          │
└───────┬───────────────────┘
        │
        ↓
┌───────────────┐
│   MongoDB     │ 9 collections
└───────────────┘

    All on Kubernetes
```

---

## SLIDE 5: CÔNG NGHỆ SỬ DỤNG

**Stream Processing:**
- Apache Spark Structured Streaming 3.5.0
- Apache Kafka (Strimzi) 3.4.0

**Storage:**
- MongoDB (Bitnami) - NoSQL

**Orchestration:**
- Kubernetes (Minikube)
- Docker containerization

**Programming:**
- Python 3.10
- PySpark, kafka-python, pandas

---

## SLIDE 6: STREAMING PIPELINE

**3 Luồng Xử Lý Song Song:**

1. **Enriched Events Stream**
   - Join với product catalog
   - Join với category hierarchy
   - Thêm user dimension

2. **Event Aggregations Stream**
   - Window: 5 seconds tumbling
   - Metrics: count, revenue theo event_type

3. **User Session Analytics Stream**
   - Window: 30 minutes session
   - Metrics: events/session, revenue/session, conversion

---

## SLIDE 7: BATCH ANALYTICS

**6 Loại Phân Tích:**

1. **Customer Journey** - Hành trình mua hàng
2. **Funnel Analysis** - Tỷ lệ chuyển đổi
3. **RFM Segmentation** - Phân khúc khách hàng
4. **Category Performance** - Hiệu suất danh mục
5. **Time Patterns** - Phân tích theo thời gian
6. **Product Recommendations** - Gợi ý sản phẩm

---

## SLIDE 8: KỸ THUẬT NỔI BẬT

**1. Window Operations**
- Tumbling window: Fixed 5s intervals
- Session window: 30 min timeout

**2. Join Optimization**
- Broadcast join cho dimension tables
- Stream-stream join với watermark

**3. State Management**
- Sessionization với stateful processing
- Checkpoint cho fault tolerance

**4. Late Data Handling**
- Watermarking: 10 minutes
- Late events vẫn được xử lý

---

## SLIDE 9: KẾT QUẢ DEMO

**Streaming Performance:**
- Input rate: 1,000 events/giây
- Processing time: 5-8 giây/batch
- End-to-end latency: <10 giây
- Records/batch: ~30,000

**Batch Performance:**
- 10M events phân tích trong ~5 phút
- K-means clustering: 100K users trong 2 phút

**Storage:**
- MongoDB: 3GB sau 1 triệu events
- 9 collections với analytics khác nhau

---

## SLIDE 10: INSIGHTS BUSINESS

**Ví dụ từ Funnel Analysis:**
```
View: 100,000 users (100%)
  ↓ 5% conversion
Cart: 5,000 users (5%)
  ↓ 40% conversion
Purchase: 2,000 users (2%)
```
→ **Cần cải thiện cart → purchase conversion!**

**RFM Segmentation:**
- Champions: 15% customers, 40% revenue
- At Risk: 20% customers, cần re-engagement
- Hibernating: 25% customers, potential churn

---

## SLIDE 11: KUBERNETES DEPLOYMENT

**Pods Running:**
- MongoDB: 1 replica
- Kafka: 1 broker + 1 zookeeper
- Spark Streaming: 1 driver + executors
- Strimzi Operator: 1 pod

**Resource Allocation:**
- Total: 4 CPUs, 8GB RAM
- Spark Driver: 2 cores, 2GB
- Spark Executor: 2 cores, 2GB

**Features:**
- Auto-restart on failure
- Rolling updates
- Resource limits

---

## SLIDE 12: CODE STRUCTURE

```
bigdata_project/
├── src/
│   ├── streaming/    # 3 Spark streaming apps
│   ├── batch/        # 2 batch analytics
│   └── utils/        # Simulator, generators
├── data/
│   ├── raw/          # CSV dataset 5.3GB
│   └── catalog/      # Dimension tables
├── config/
│   ├── .env          # Configuration
│   └── kafka-strimzi.yaml
├── kubernetes/       # K8s manifests
├── scripts/          # Deployment automation
└── docs/             # Documentation
```

---

## SLIDE 13: CHALLENGES & SOLUTIONS

| Challenge | Solution |
|-----------|----------|
| Memory OOM | Broadcast join cho dimension tables |
| Kafka version mismatch | Download đúng JAR files |
| Session window complexity | 30 min timeout với watermark |
| Late data handling | Watermarking 10 minutes |
| Container size | Multi-stage Docker build |

---

## SLIDE 14: MỞ RỘNG TƯƠNG LAI

**Technical:**
- Real-time recommendations với ALS
- Anomaly detection với ML
- A/B testing framework
- Lambda architecture với Delta Lake

**Infrastructure:**
- Scale to AWS EMR + MSK + DocumentDB
- Monitoring với Grafana + Prometheus
- Multi-region deployment
- Auto-scaling

---

## SLIDE 15: BÀI HỌC

**Technical Skills:**
✅ Spark Structured Streaming
✅ Kafka architecture
✅ Kubernetes orchestration
✅ MongoDB aggregation

**Data Engineering:**
✅ Pipeline design patterns
✅ Stream vs batch tradeoffs
✅ Monitoring distributed systems
✅ Schema evolution

**Soft Skills:**
✅ Documentation
✅ Debugging
✅ Code organization

---

## SLIDE 16: KẾT LUẬN

**Đã hoàn thành:**
- ✅ Complete data pipeline: Kafka → Spark → MongoDB
- ✅ Real-time processing: <10s latency
- ✅ Batch analytics: 6 loại phân tích
- ✅ Kubernetes deployment: Production-ready
- ✅ Documentation: Đầy đủ, chi tiết

**Kết quả:**
- System xử lý 42M events
- 9 collections analytics
- Scalable architecture
- Real business insights

---

## SLIDE 17: Q&A

```
          ❓
   CÂU HỎI & TRẢ LỜI
          
     📧 Email: [your-email]
     🔗 GitHub: [your-github]
     📁 Code: github.com/[repo]
```

---

## SLIDE 18: THANK YOU

```
       🎉 CẢM ƠN THẦY/CÔ 
         ĐÃ THEO DÕI!
         
         
       💻 LIVE DEMO
         
         
    Sẵn sàng trả lời câu hỏi
```

---

## 📝 NOTES CHO TỪNG SLIDE

**Slide 4 (Architecture):** 
- Vẽ diagram rõ ràng, có mũi tên chỉ data flow
- Highlight components chính

**Slide 9 (Kết quả):**
- Show actual numbers từ system
- Screenshot Spark UI nếu được

**Slide 10 (Business Insights):**
- Đây là slide QUAN TRỌNG nhất
- Show giá trị thực tế của project

**Slide 13 (Challenges):**
- Show rằng bạn gặp khó khăn và giải quyết được
- Giáo viên thích điều này!

---

## 🎨 DESIGN TIPS

**Colors:**
- Title slides: Dark blue background
- Content slides: White background
- Code blocks: Light gray background
- Highlights: Orange/Red cho important points

**Fonts:**
- Title: 44pt, bold
- Headers: 32pt, semi-bold
- Body: 20-24pt, regular
- Code: Monospace, 18pt

**Images:**
- Architecture diagram: PHẢI CÓ
- Screenshots: Spark UI, MongoDB data
- Terminal outputs: Chọn lọc, không quá nhiều text

---

## ⏱️ TIMING

- Slide 1-3: 2 phút (intro)
- Slide 4-8: 5 phút (technical)
- **Slide 9-10: 3 phút (results - QUAN TRỌNG)**
- Slide 11-14: 3 phút (deployment & future)
- Slide 15-16: 2 phút (conclusion)

**Total: 15 phút + Demo 10 phút = 25 phút**

---

## 💡 PRESENTATION TIPS

1. **Slide 10 (Business Insights):** Dành nhiều thời gian nhất
2. **Không đọc slides:** Nhìn vào giáo viên, tự nhiên
3. **Pointer:** Dùng con trỏ chuột chỉ vào diagrams
4. **Transition:** Smooth, không quá nhiều animation
5. **Backup slides:** Thêm 5-10 slides kỹ thuật chi tiết (nếu hỏi)

**GOOD LUCK! 🚀**
