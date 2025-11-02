# Bắt đầu từ image Spark 3.5.0 CÓ SẴN Python
FROM apache/spark:3.5.0-python3

# Chuyển sang user 'root' để cài đặt các gói
USER root

# -----------------------------------------------------------------
# BƯỚC 1: Cài đặt thư viện Python
# -----------------------------------------------------------------
RUN pip install pandas kafka-python

# -----------------------------------------------------------------
# BƯỚC 2: Tải sẵn (Pre-download) các file JARs
# -----------------------------------------------------------------
# Gói Kafka
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.0/spark-sql-kafka-0-10_2.12-3.5.0.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.0/spark-token-provider-kafka-0-10_2.12-3.5.0.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar

# Gói MongoDB
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.3.0/mongo-spark-connector_2.12-10.3.0.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/mongodb/mongodb-driver-sync/4.8.2/mongodb-driver-sync-4.8.2.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/mongodb/bson/4.8.2/bson-4.8.2.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/mongodb/mongodb-driver-core/4.8.2/mongodb-driver-core-4.8.2.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/mongodb/bson-record-codec/4.8.2/bson-record-codec-4.8.2.jar

# Gói phụ thuộc chung
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

# -----------------------------------------------------------------
# BƯỚC 3: Copy script
# -----------------------------------------------------------------
RUN echo "Cache bust v7" # <-- THÊM DÒNG NÀY ĐỂ PHÁ VỠ CACHE
COPY streaming_app_k8s.py /opt/spark/work-dir/streaming_app.py
# Trả lại quyền cho user 'spark' (user mặc định)
USER $SPARK_UID