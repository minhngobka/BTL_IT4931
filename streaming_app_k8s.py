import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, TimestampType

# --- Cấu hình ---

# 1. Thông tin Kafka (Lấy từ Giai đoạn 1)
# Sửa lại IP và Port của bạn
KAFKA_BOOTSTRAP_SERVER = "my-cluster-kafka-bootstrap.default.svc.cluster.local:9092"
KAFKA_TOPIC = "customer_events"

# 2. Thông tin MongoDB (Chúng ta sẽ dùng port-forward)
MONGO_URI = "mongodb://my-mongo-mongodb.default.svc.cluster.local:27017/"
MONGO_DB_NAME = "bigdata_db"
MONGO_COLLECTION_NAME = "customer_events"

# 3. Cấu hình các gói JAR cần thiết


def main():
    print("Khởi tạo Spark Session...")
    
    # Khởi tạo SparkSession
    spark = SparkSession.builder \
        .appName("CustomerJourneyStreaming") \
        .master("local[*]") \
        .config("spark.mongodb.write.connection.uri", MONGO_URI)  \
        .config("spark.mongodb.write.database", MONGO_DB_NAME) \
        .config("spark.mongodb.write.collection", MONGO_COLLECTION_NAME) \
        .getOrCreate()

    # Giảm log của Spark để dễ đọc
    spark.sparkContext.setLogLevel("WARN")
    print("Spark Session đã sẵn sàng.")

    # 1. Đọc luồng (Read Stream) từ Kafka
    df_kafka = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    print("Đã kết nối với Kafka topic. Đang chờ dữ liệu...")

    # 2. Định nghĩa Schema (Cấu trúc) cho dữ liệu JSON
    # Phải khớp với các cột trong file CSV của bạn
    schema = StructType([
        StructField("event_time", StringType()), # Sẽ convert sau
        StructField("event_type", StringType()),
        StructField("product_id", LongType()),
        StructField("category_id", LongType()),
        StructField("brand", StringType()),
        StructField("price", DoubleType()),
        StructField("user_id", LongType()),
        StructField("user_session", StringType())
    ])

    # 3. Biến đổi (Transformations)
    df_events = df_kafka.select(
        # Chuyển cột 'value' (dạng binary) thành String, sau đó parse JSON
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    # Xử lý dữ liệu
    df_processed = df_events \
        .withColumn("event_timestamp", col("event_time").cast(TimestampType())) \
        .withColumn("processing_timestamp", current_timestamp()) \
        .drop("event_time") # Xóa cột string cũ

    # Áp dụng Watermarking (Yêu cầu đề bài)
    # Xử lý dữ liệu trễ 10 phút
    df_with_watermark = df_processed \
        .withWatermark("event_timestamp", "10 minutes")

    print("Đã định nghĩa schema và transform. Bắt đầu ghi luồng...")

    # 4. Ghi luồng (Write Stream) vào MongoDB
    # Dùng 'foreachBatch' là cách linh hoạt nhất
    def write_to_mongo(batch_df, epoch_id):
        print(f"--- Đang ghi Epoch {epoch_id} ---")
        if batch_df.count() > 0:
            batch_df.write \
                .format("mongodb") \
                .mode("append") \
                .save() # <-- Xóa các .option() đi, nó sẽ tự lấy config global
            print(f"--- Đã ghi {batch_df.count()} dòng vào MongoDB ---")
        else:
            print("--- Không có dữ liệu mới trong epoch này ---")

    query = df_with_watermark.writeStream \
        .foreachBatch(write_to_mongo) \
        .outputMode("update") \
        .option("checkpointLocation", "/opt/spark/work-dir/checkpoints") \
        .trigger(processingTime="15 seconds") \
        .start()

    print("=== Ứng dụng Spark Streaming đang chạy ===")
    print("=== Dữ liệu từ Kafka sẽ được xử lý và lưu vào MongoDB ===")
    print("=== Nhấn Ctrl+C để dừng ===")
    
    query.awaitTermination()

if __name__ == "__main__":
    main()