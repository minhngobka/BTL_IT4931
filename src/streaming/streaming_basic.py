import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, TimestampType

# Load environment variables from config/.env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

# --- Cấu hình ---

# 1. Thông tin Kafka (Đọc từ .env hoặc mặc định)
KAFKA_BOOTSTRAP_SERVER = os.getenv('KAFKA_INTERNAL_BROKER', 'my-cluster-kafka-bootstrap.default.svc.cluster.local:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'customer_events')

# 2. Thông tin MongoDB (Đọc từ .env hoặc mặc định)
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://my-mongo-mongodb.default.svc.cluster.local:27017/')
MONGO_DB_NAME = os.getenv('MONGODB_DATABASE', 'bigdata_db')
MONGO_COLLECTION_NAME = "customer_events"
SPARK_CHECKPOINT_DIR = os.getenv('SPARK_CHECKPOINT_DIR', './checkpoints')#Thêm 

def main():
    print("Khởi tạo Spark Session...")
    
    # Khởi tạo SparkSession
    spark = SparkSession.builder \
        .appName("CustomerJourneyStreaming") \
        .master("local[*]") \
        .config("spark.mongodb.output.uri", f"{MONGO_URI}{MONGO_DB_NAME}.{MONGO_COLLECTION_NAME}") \
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
        if batch_df.count() == 0:
            print("--- Không có dữ liệu mới trong epoch này ---")
            return

        # 1. Ghi toàn bộ event vào MongoDB collection 'customer_events'
        batch_df.write \
            .format("mongodb") \
            .mode("append") \
            .option("uri", MONGO_URI) \
            .option("database", MONGO_DB_NAME) \
            .option("collection", MONGO_COLLECTION_NAME) \
            .save()

        print(f"--- Đã ghi {batch_df.count()} dòng vào collection 'customer_events' ---")

        # 2. Lưu unique sản phẩm vào 'product_catalog'
        try:
            # Chuyển batch_df thành Pandas để duyệt
            pdf = batch_df.select("product_id", "category_id", "brand", "price").distinct().toPandas()

            client = MongoClient(MONGO_URI)
            catalog_col = client[MONGO_DB_NAME]["product_catalog"]

            for _, row in pdf.iterrows():
                product_id = int(row["product_id"])
                name = f"Product {product_id}"
                img = f"https://via.placeholder.com/300x300/FF6B6B/FFFFFF?text=Product+{product_id}"

                catalog_col.update_one(
                    {"product_id": product_id},
                    {"$setOnInsert": {
                        "product_id": product_id,
                        "product_name": name,
                        "category_id": int(row["category_id"]),
                        "brand": row["brand"],
                        "price": float(row["price"]),
                        "image_url": img
                    }},
                    upsert=True
                )
            print(f"✓ Đã cập nhật product_catalog với {len(pdf)} sản phẩm")
        except Exception as e:
            print(f"⚠ Lỗi khi cập nhật product_catalog: {e}")


    query = df_with_watermark.writeStream \
        .foreachBatch(write_to_mongo) \
        .outputMode("update") \
        .option("checkpointLocation", SPARK_CHECKPOINT_DIR) \
        .trigger(processingTime="15 seconds") \
        .start()

    print("=== Ứng dụng Spark Streaming đang chạy ===")
    print("=== Dữ liệu từ Kafka sẽ được xử lý và lưu vào MongoDB ===")
    print("=== Nhấn Ctrl+C để dừng ===")
    
    query.awaitTermination()

if __name__ == "__main__":
    main()