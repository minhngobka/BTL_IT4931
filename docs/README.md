# Big Data Customer Journey Analytics# 🚀 Bài tập lớn: Phân tích Hành trình Khách hàng (Customer Journey)



Real-time customer behavior analysis using **Apache Spark**, **Kafka**, and **MongoDB** on **Kubernetes**.Dự án này xây dựng một hệ thống Big Data theo kiến trúc Kappa để phân tích hành vi người dùng trên một trang thương mại điện tử (view, cart, purchase) theo thời gian thực.



------



## 🚀 Quick Start## � Quick Links for Team Members



```bash**Choose your path:**

# 1. Clone

git clone https://github.com/minhngobka/BTL_IT4931.git && cd BTL_IT4931- 🚀 **[QUICK_CLONE_AND_RUN.md](QUICK_CLONE_AND_RUN.md)** - Fastest setup (copy-paste commands)

- 📖 **[SETUP_FOR_TEAMMATES.md](SETUP_FOR_TEAMMATES.md)** - Complete step-by-step guide with explanations

# 2. Get dataset (download 2019-Oct.csv from Kaggle)- ⚙️ **[ENV_SETUP.md](ENV_SETUP.md)** - Environment variables configuration

# https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store- 🔧 **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Detailed deployment reference

- 📊 **[README_ADVANCED.md](README_ADVANCED.md)** - Technical architecture documentation

# 3. Setup

python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt---



# 4. Deploy## �🛠️ Yêu cầu cài đặt (Prerequisites)

minikube start --cpus=4 --memory=8192

./run_project_step_by_step.shTrước khi bắt đầu, bạn cần cài đặt các công cụ sau trên máy Ubuntu:



# 5. Run1.  **Git:** `sudo apt install git`

cp .env.example .env  # Update KAFKA_EXTERNAL_BROKER with minikube ip:port2.  **Docker:** [Link hướng dẫn cài Docker](https://docs.docker.com/engine/install/ubuntu/)

python simulator.py3.  **Python 3.10+ & Venv:** `sudo apt install python3.10-venv`

```4.  **Minikube:** [Link hướng dẫn cài Minikube](https://minikube.sigs.k8s.io/docs/start/)

5.  **Kubectl:** `sudo snap install kubectl --classic`

**⏱️ Time: ~25 minutes** | 📖 **Full guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)6.  **Helm:** `sudo snap install helm --classic`



---## 📦 Cài đặt dự án



## 📊 What It Does### 1. Clone Repository



Analyzes e-commerce behavior (views, carts, purchases) in real-time:```bash

git clone https://github.com/minhngobka/BTL_IT4931.git

```cd BTL_IT4931

CSV → Kafka → Spark Streaming → MongoDB```

              (enrich, aggregate, ML)

```### 2. Thiết lập Môi trường Python



**Outputs:**```bash

- 🛍️ **20K+ enriched events** (product details + user actions)# Tạo môi trường ảo

- 📈 **4K+ window aggregations** (5-min, 10-min windows)python3 -m venv venv

- 👤 **8K+ session analytics** (user journey tracking)

- 🎯 **100+ conversion funnels** (view→cart→purchase rates)# Kích hoạt môi trường

- 🤖 **ML insights** (K-Means clusters, churn predictions)source venv/bin/activate



---# Cài đặt thư viện (nếu có file requirements.txt)

# (Bạn có thể tạo file này bằng lệnh: pip freeze > requirements.txt)

## 🏗️ Architecturepip install pandas kafka-python

```

**Stack:** Spark 3.5 | Kafka (Strimzi) | MongoDB | Kubernetes (Minikube)

### 3. Tải Dữ liệu (Rất quan trọng)

```

CSV Simulator → Kafka Topic → Spark Streaming → MongoDB CollectionsDo file dữ liệu quá lớn, nó không được lưu trên GitHub. Bạn cần tự tải file `2019-Oct.csv` từ link Kaggle dưới đây:

                               ↓ (batch)

                            ML Analytics* **Link Kaggle:** [https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store)

```

Sau khi tải về, hãy **đặt file `2019-Oct.csv` vào thư mục gốc của dự án** (ngang hàng với file `simulator.py`).

**Key Features:**

- Complex windowed aggregations (tumbling, sliding)## 🚀 Khởi chạy Hạ tầng (Giai đoạn 1)

- Stream-static joins (broadcast)

- Custom UDFs & feature engineeringCác lệnh này chỉ cần chạy 1 lần để thiết lập môi trường Kubernetes.

- Stateful session tracking

- Exactly-once semantics### 1. Khởi động Minikube

- K-Means & Random Forest ML

```bash

📖 **Details:** [TECHNICAL_DOCS.md](TECHNICAL_DOCS.md)minikube start --driver=docker --cpus=4 --memory=8g

```

---

### 2. Cài đặt MongoDB

## 📁 Key Files

```bash

```helm repo add bitnami [https://charts.bitnami.com/bitnami](https://charts.bitnami.com/bitnami)

simulator.py                 # Kafka producerhelm install my-mongo bitnami/mongodb --set auth.enabled=false

streaming_app_advanced.py    # Real-time processing```

batch_analytics_ml.py        # ML analytics

k8s-spark-apps.yaml         # Kubernetes config### 3. Cài đặt Strimzi (Kafka Operator)

run_project_step_by_step.sh # Automated deployment

``````bash

helm repo add strimzi [https://strimzi.io/charts/](https://strimzi.io/charts/)

---helm install strimzi-operator strimzi/strimzi-kafka-operator

```

## 🔍 Quick Commands

### 4. Đợi các Operator chạy

```bash

# StatusDùng VSCode mở một Terminal mới (Ctrl + Shift + \`) và chạy:

kubectl get pods```bash

kubectl get pods -w

# Logs```

kubectl logs -f deployment/spark-streaming-advancedĐợi cho đến khi cả `my-mongo-mongodb-...` và `strimzi-cluster-operator-...` đều `Running`.



# MongoDB### 5. Tạo Kafka Cluster (KRaft)

kubectl port-forward service/my-mongo-mongodb 27017:27017

mongosh mongodb://localhost:27017 --eval "db.getSiblingDB('bigdata_db').enriched_events.countDocuments()"Sau khi operator đã chạy, hãy áp dụng file cấu hình Kafka của chúng ta:

```bash

# Spark UIkubectl apply -f kafka-combined.yaml

kubectl port-forward service/spark-streaming-svc 4040:4040  # http://localhost:4040```

Tiếp tục theo dõi `kubectl get pods -w`. Đợi cho đến khi các pod `my-cluster-kafka-0` và `my-cluster-entity-operator-...` cũng `Running`.

# Run batch ML

kubectl create job spark-batch-manual --from=cronjob/spark-batch-ml-scheduled---

```

## 🏃 Chạy Mô phỏng (Data Simulator)

---

Sau khi toàn bộ hạ tầng đã `Running`:

## 🛠️ Prerequisites

### 1. Tìm địa chỉ Kafka

**Required:**

- Docker (20.0+), Minikube (1.25+), kubectl, Helm (3.0+), Python 3.10+```bash

# Lấy IP của Minikube

**Quick install (Ubuntu):**minikube ip

```bash

sudo apt install docker.io -y && sudo usermod -aG docker $USER# Lấy Cổng (Port) của Kafka

curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64kubectl get service my-cluster-kafka-external-bootstrap -o=jsonpath='{.spec.ports[0].nodePort}'

sudo install minikube-linux-amd64 /usr/local/bin/minikube```

sudo snap install kubectl --classic && sudo snap install helm --classic

```### 2. Cập nhật file `simulator.py`



---Mở file `simulator.py` và cập nhật dòng `KAFKA_BROKER` bằng IP và Cổng bạn vừa tìm được:



## 🆘 Troubleshooting```python

# Ví dụ:

| Problem | Solution |KAFKA_BROKER = '192.168.49.2:31234'

|---------|----------|```

| Simulator won't connect | Check `.env` has correct `KAFKA_EXTERNAL_BROKER=$(minikube ip):31927` |

| Pods stuck | `minikube delete && minikube start --cpus=4 --memory=8192` |### 3. Chạy script

| Docker build fails | `eval $(minikube docker-env) && docker build -t bigdata-spark:latest .` |

(Đảm bảo bạn vẫn đang trong môi trường `venv`)

**More:** [SETUP_GUIDE.md#troubleshooting](SETUP_GUIDE.md#troubleshooting)```bash

python3 simulator.py

---```

Bạn sẽ thấy script bắt đầu gửi dữ liệu lên Kafka.

## 📚 Documentation

Giai đoạn 3: Xây dựng Docker Image

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Installation & deployment

- **[TECHNICAL_DOCS.md](TECHNICAL_DOCS.md)** - Architecture & features  Mở một terminal mới (terminal cũ vẫn đang chạy simulator.py).

- **[.env.example](.env.example)** - Configuration template

1. Trỏ Terminal vào Docker của Minikube

---

Đây là bước cực kỳ quan trọng. Image phải được build trực tiếp vào bên trong môi trường Docker của Minikube.

## 🎓 Academic Info

eval $(minikube docker-env)

**Project:** Real-time Customer Journey Analytics using Kappa Architecture  

**Demonstrates:** Advanced Spark Streaming, ML integration, Kubernetes deployment

2. Build Docker Image

**Features Coverage:**

✅ Complex aggregations | ✅ Joins | ✅ UDFs | ✅ State management  Build image chứa ứng dụng Spark, các file JAR và cả 3 script Python. (Chúng ta dùng v1.0 làm ví dụ).

✅ Windows | ✅ ML (K-Means, Random Forest) | ✅ Production patterns

docker build -t customer-journey-app:v1.0 .

---



**Ready? Start here:** [SETUP_GUIDE.md](SETUP_GUIDE.md) 🚀(Lưu ý: Bạn có thể đặt tên tag bất kỳ, ví dụ v15 như bạn đã làm)


⚡ Giai đoạn 4: Chạy các Job Spark trên Kubernetes

Chúng ta sẽ submit 3 job Spark song song. Job 1 và 2 là job Streaming (chạy liên tục), Job 3 là job Batch (chạy 1 lần rồi kết thúc).

Job 1: (Streaming) Thu thập dữ liệu thô

Job này đọc từ Kafka và lưu dữ liệu thô vào collection customer_events.

spark-submit \
--master k8s://https://$(minikube ip):8443 \
--deploy-mode cluster \
--name streaming-raw-ingestion \
--conf spark.kubernetes.authenticate.driver.serviceAccountName=default \
--conf spark.kubernetes.container.image=customer-journey-app:v1.0 \
--conf spark.kubernetes.container.image.pullPolicy=Never \
local:///opt/spark/work-dir/streaming_app.py


Job 2: (Streaming) Tổng hợp dữ liệu (Join + Aggregation)

Job này đọc từ Kafka, join với file CSV, và lưu kết quả tổng hợp vào collection event_counts_by_category.

spark-submit \
--master k8s://https://$(minikube ip):8443 \
--deploy-mode cluster \
--name streaming-aggregation \
--conf spark.kubernetes.authenticate.driver.serviceAccountName=default \
--conf spark.kubernetes.container.image=customer-journey-app:v1.0 \
--conf spark.kubernetes.container.image.pullPolicy=Never \
local:///opt/spark/work-dir/streaming_app_k8s.py


Job 3: (Batch) Phân tích Hành trình Khách hàng

Job này đọc toàn bộ dữ liệu từ customer_events (do Job 1 ghi vào), dùng Window Functions để phân tích và lưu kết quả phễu (funnel) vào collection journey_metrics.

spark-submit \
--master k8s://https://$(minikube ip):8443 \
--deploy-mode cluster \
--name customer-journey-batch \
--conf spark.kubernetes.authenticate.driver.serviceAccountName=default \
--conf spark.kubernetes.container.image=customer-journey-app:v1.0 \
--conf spark.kubernetes.container.image.pullPolicy=Never \
local:///opt/spark/work-dir/journey_analysis.py


4. Theo dõi ứng dụng

Mở một terminal thứ ba để theo dõi các pod.

kubectl get pods -w


Bạn sẽ thấy 3 pod driver được tạo:

streaming-raw-ingestion-...-driver: Sẽ ở trạng thái Running.

streaming-aggregation-...-driver: Sẽ ở trạng thái Running.

customer-journey-batch-...-driver: Sẽ chuyển sang Running rồi Completed.

Gỡ lỗi:

ErrImageNeverPull: Bạn đã quên chạy eval $(minikube docker-env) trước khi docker build.

Error / Completed (ngay lập tức): Dùng kubectl logs <tên-pod-driver> để xem lỗi.

📊 Giai đoạn 5: Kiểm tra Kết quả

Dữ liệu của bạn bây giờ nằm ở 3 collection khác nhau trong MongoDB.

1. Kết nối với MongoDB

Dùng MongoDB Compass hoặc Command Line.

# Lấy tên pod MongoDB
kubectl get pods | grep my-mongo

# Port-forward (thay tên pod của bạn)
kubectl port-forward <my-mongo-mongodb-pod-name> 27017:27017


Mở Compass kết nối tới mongodb://localhost:27017/ và xem database bigdata_db.

Hoặc dùng kubectl exec:

# Truy cập shell (thay tên pod của bạn)
kubectl exec -it <my-mongo-mongodb-pod-name> -- mongosh

# Bên trong mongosh:
use bigdata_db;


2. Xem các Collection

// 1. Dữ liệu thô (từ Job 1)
db.customer_events.find().limit(5);

// 2. Dữ liệu tổng hợp (từ Job 2)
db.event_counts_by_category.find().limit(5);

// 3. Kết quả phân tích hành trình (từ Job 3)
db.journey_metrics.find().pretty();


🛑 Giai đoạn 6: Dừng Hệ thống

Sau khi hoàn tất, hãy dọn dẹp tài nguyên:

# 1. Dừng simulator (Ctrl + C)

# 2. Xóa các job Spark (Deployment)
# (spark-submit tự xóa pod khi deploy-mode=cluster, nhưng ta nên xóa hẳn app)
# Bạn có thể dùng tên app (spark-app-name) hoặc tên pod driver để xóa
kubectl delete pod streaming-raw-ingestion-driver
kubectl delete pod streaming-aggregation-driver
# (Pod 'customer-journey-batch' đã 'Completed' nên không cần xóa)

# 3. Xóa Kafka
kubectl delete -f kafka-combined.yaml

# 4. Gỡ cài đặt Strimzi và MongoDB
helm uninstall strimzi-operator
helm uninstall my-mongo

# 5. Dừng Minikube
minikube stop
