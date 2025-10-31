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
python simulator.py
```
Bạn sẽ thấy script bắt đầu gửi dữ liệu lên Kafka.