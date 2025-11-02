# 🚀 Bài tập lớn: Phân tích Hành trình Khách hàng (Customer Journey)

Dự án này xây dựng một hệ thống Big Data theo kiến trúc Kappa để phân tích hành vi người dùng trên một trang thương mại điện tử (view, cart, purchase) theo thời gian thực.

## 🛠️ Yêu cầu cài đặt (Prerequisites)

Trước khi bắt đầu, bạn cần cài đặt các công cụ sau trên máy Ubuntu:

1.  **Git:** `sudo apt install git`
2.  **Docker:** [Link hướng dẫn cài Docker](https://docs.docker.com/engine/install/ubuntu/)
3.  **Python 3.10+ & Venv:** `sudo apt install python3.10-venv`
4.  **Minikube:** [Link hướng dẫn cài Minikube](https://minikube.sigs.k8s.io/docs/start/)
5.  **Kubectl:** `sudo snap install kubectl --classic`
6.  **Helm:** `sudo snap install helm --classic`

## 📦 Cài đặt dự án

### 1. Clone Repository

```bash
git clone https://github.com/DucTham2004/bigdata-customer-journey.git
cd bigdata_project
```

### 2. Thiết lập Môi trường Python

```bash
# Tạo môi trường ảo
python3 -m venv venv

# Kích hoạt môi trường
source venv/bin/activate

# Cài đặt thư viện (nếu có file requirements.txt)
# (Bạn có thể tạo file này bằng lệnh: pip freeze > requirements.txt)
pip install pandas kafka-python
```

### 3. Tải Dữ liệu (Rất quan trọng)

Do file dữ liệu quá lớn, nó không được lưu trên GitHub. Bạn cần tự tải file `2019-Oct.csv` từ link Kaggle dưới đây:

* **Link Kaggle:** [https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store)

Sau khi tải về, hãy **đặt file `2019-Oct.csv` vào thư mục gốc của dự án** (ngang hàng với file `simulator.py`).

## 🚀 Khởi chạy Hạ tầng (Giai đoạn 1)

Các lệnh này chỉ cần chạy 1 lần để thiết lập môi trường Kubernetes.

### 1. Khởi động Minikube

```bash
minikube start --driver=docker --cpus=4 --memory=8g
```

### 2. Cài đặt MongoDB

```bash
helm repo add bitnami [https://charts.bitnami.com/bitnami](https://charts.bitnami.com/bitnami)
helm install my-mongo bitnami/mongodb --set auth.enabled=false
```

### 3. Cài đặt Strimzi (Kafka Operator)

```bash
helm repo add strimzi [https://strimzi.io/charts/](https://strimzi.io/charts/)
helm install strimzi-operator strimzi/strimzi-kafka-operator
```

### 4. Đợi các Operator chạy

Dùng VSCode mở một Terminal mới (Ctrl + Shift + \`) và chạy:
```bash
kubectl get pods -w
```
Đợi cho đến khi cả `my-mongo-mongodb-...` và `strimzi-cluster-operator-...` đều `Running`.

### 5. Tạo Kafka Cluster (KRaft)

Sau khi operator đã chạy, hãy áp dụng file cấu hình Kafka của chúng ta:
```bash
kubectl apply -f kafka-combined.yaml
```
Tiếp tục theo dõi `kubectl get pods -w`. Đợi cho đến khi các pod `my-cluster-kafka-0` và `my-cluster-entity-operator-...` cũng `Running`.

---

## 🏃 Chạy Mô phỏng (Data Simulator)

Sau khi toàn bộ hạ tầng đã `Running`:

### 1. Tìm địa chỉ Kafka

```bash
# Lấy IP của Minikube
minikube ip

# Lấy Cổng (Port) của Kafka
kubectl get service my-cluster-kafka-external-bootstrap -o=jsonpath='{.spec.ports[0].nodePort}'
```

### 2. Cập nhật file `simulator.py`

Mở file `simulator.py` và cập nhật dòng `KAFKA_BROKER` bằng IP và Cổng bạn vừa tìm được:

```python
# Ví dụ:
KAFKA_BROKER = '192.168.49.2:31234'
```

### 3. Chạy script

(Đảm bảo bạn vẫn đang trong môi trường `venv`)
```bash
python3 simulator.py
```
Bạn sẽ thấy script bắt đầu gửi dữ liệu lên Kafka.

Giai đoạn 3: Xây dựng & Chạy Spark Streaming
Mở một terminal mới (terminal cũ vẫn đang chạy simulator).

1. Trỏ Terminal vào Docker của Minikube
Đây là bước cực kỳ quan trọng. Do chúng ta dùng pullPolicy=Never, image phải được build trực tiếp vào bên trong môi trường Docker của Minikube.

Bash

eval $(minikube docker-env)
Terminal của bạn bây giờ đã kết nối với Docker daemon của Minikube.

2. Build Docker Image
Build image chứa ứng dụng Spark, các file JAR và script Python. (Chúng ta dùng v1 làm ví dụ).

Bash

docker build -t spark-streaming-app:v1 .
3. Submit Ứng dụng Spark lên Kubernetes
Chạy lệnh spark-submit để khởi động ứng dụng streaming. Lệnh này sẽ yêu cầu Kubernetes tạo một pod driver mới sử dụng image chúng ta vừa build.

Bash

spark-submit \
--master k8s://https://$(minikube ip):8443 \
--deploy-mode cluster \
--name customer-journey-streaming \
--conf spark.kubernetes.authenticate.driver.serviceAccountName=default \
--conf spark.kubernetes.container.image=spark-streaming-app:v1 \
--conf spark.kubernetes.container.image.pullPolicy=Never \
local:///opt/spark/work-dir/streaming_app.py
4. Theo dõi ứng dụng
Mở một terminal thứ ba để theo dõi các pod.

Bash

kubectl get pods -w
Bạn sẽ thấy pod customer-journey-streaming-...-driver được tạo. Nếu nó chuyển sang trạng thái Running và giữ nguyên trạng thái đó, nghĩa là ứng dụng đã chạy thành công!

Gỡ lỗi:

Nếu pod bị ErrImageNeverPull: Bạn đã quên chạy eval $(minikube docker-env) trước khi docker build.

Nếu pod chuyển sang Error hoặc Completed ngay lập tức: Dùng kubectl logs <tên-pod-driver> để xem lỗi (thường là lỗi Python hoặc lỗi kết nối).

📊 Giai đoạn 4: Kiểm tra Kết quả
Nếu cả simulator và pod Spark đều đang Running, dữ liệu sẽ được xử lý và lưu vào MongoDB.

Cách 1: Sử dụng Công cụ GUI (như MongoDB Compass)
Tìm tên pod MongoDB:

Bash

kubectl get pods
(Ví dụ: my-mongo-mongodb-54c5b97b6b-b6kld)

Chuyển tiếp (port-forward) cổng 27017 của pod ra máy local:

Bash

kubectl port-forward my-mongo-mongodb-54c5b97b6b-b6kld 27017:27017
Mở MongoDB Compass và kết nối tới mongodb://localhost:27017/.

Bạn sẽ thấy database bigdata_db và collection customer_events chứa đầy dữ liệu.

Cách 2: Sử dụng Command Line (mongosh)
Truy cập shell bên trong pod MongoDB:

Bash

kubectl exec -it my-mongo-mongodb-54c5b97b6b-b6kld -- mongosh
Bên trong mongosh, chạy các lệnh sau để kiểm tra:

JavaScript

// Chuyển sang database
use bigdata_db;

// Đếm số lượng tài liệu
db.customer_events.countDocuments();

// Xem 5 tài liệu mẫu
db.customer_events.find().limit(5);
🛑 Dừng Hệ thống
Sau khi hoàn tất, hãy dọn dẹp tài nguyên:

Bash

# 1. Dừng simulator và spark-submit (Ctrl + C)
# 2. Xóa pod Spark (nếu nó vẫn chạy)
kubectl delete pod <tên-pod-driver>

# 3. Xóa Kafka
kubectl delete -f kafka-combined.yaml

# 4. Gỡ cài đặt Strimzi và MongoDB
helm uninstall strimzi-operator
helm uninstall my-mongo

# 5. Dừng Minikube
minikube stop
