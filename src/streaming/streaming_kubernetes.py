import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
# Đảm bảo bạn đã import 'window'
from pyspark.sql.functions import from_json, col, current_timestamp, window
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
# Chúng ta sẽ ghi vào một collection mới
MONGO_COLLECTION_NAME = "event_counts_by_category" 


def main():
    print("Khởi tạo Spark Session...")
    
    spark = SparkSession.builder \
        .appName("CustomerJourneyStreaming") \
        .master("local[*]") \
        .config("spark.mongodb.write.connection.uri", MONGO_URI) \
        .config("spark.mongodb.write.database", MONGO_DB_NAME) \
        .config("spark.mongodb.write.collection", MONGO_COLLECTION_NAME) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    print("Spark Session đã sẵn sàng.")

    # --- BƯỚC MỚI: ĐỌC DỮ LIỆU STATIC (STATIC DATAFRAME) ---
    print("Đang đọc dữ liệu catalog sản phẩm từ /opt/spark/work-dir/product_catalog.csv ...")
    catalog_schema = StructType([
        StructField("product_id", LongType()),
        StructField("product_name", StringType()),
        StructField("category_name", StringType())
    ])
    
    df_product_catalog = spark.read \
        .schema(catalog_schema) \
        .option("header", "true") \
        .csv("/opt/spark/work-dir/product_catalog.csv")
    
    # df_product_catalog.show() # Debug
    print("Đã đọc xong catalog. Bắt đầu đọc luồng Kafka...")
    # --- KẾT THÚC BƯỚC MỚI ---

    # 1. Đọc luồng (Read Stream) từ Kafka
    df_kafka = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    # 2. Định nghĩa Schema (Cấu trúc) cho dữ liệu JSON
    schema = StructType([
        StructField("event_time", StringType()),
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
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    df_processed = df_events \
        .withColumn("event_timestamp", col("event_time").cast(TimestampType())) \
        .drop("event_time")

    df_with_watermark = df_processed \
        .withWatermark("event_timestamp", "10 minutes")

    # --- BƯỚC MỚI: JOIN LUỒNG VỚI DỮ LIỆU STATIC ---
    # YÊU CẦU: "Join Operations" (Stream-Static Join)
    print("Đang join luồng với catalog...")
    df_enriched_stream = df_with_watermark.join(
        df_product_catalog,
        "product_id", # Khóa join
        "left_outer"  # Kiểu join: giữ tất cả sự kiện, ngay cả khi không tìm thấy sản phẩm
    )
    # --- KẾT THÚC BƯỚC MỚI ---

    # 4. TÍNH TOÁN AGGREGATION TRÊN DỮ LIỆU ĐÃ JOIN
    # YÊU CẦU: "Complex Aggregations"
    print("Đang tính toán aggregation trên dữ liệu đã enrich...")
    df_windowed_counts = df_enriched_stream \
        .groupBy(
            window(col("event_timestamp"), "1 minute", "30 seconds").alias("time_window"),
            col("category_name"), # <-- DÙNG CỘT MỚI TỪ JOIN
            col("event_type")
        ) \
        .count() 
        # <--- DÒNG ORDER BY ĐÃ BỊ XÓA

    # 5. GHI KẾT QUẢ RA 2 NƠI (SINK) CÙNG LÚC

    # --- SINK 1: GHI RA CONSOLE (ĐỂ DEBUG) ---
    query_console = df_windowed_counts.writeStream \
        .outputMode("complete") \
        .format("console") \
        .option("truncate", "false") \
        .trigger(processingTime="30 seconds") \
        .start()

    # --- SINK 2: GHI VÀO MONGODB ---
    # Dùng foreachBatch để ghi vào MongoDB
    
    def write_agg_to_mongo(batch_df, epoch_id):
        print(f"--- [Mongo Sink] Đang ghi Epoch {epoch_id} ---")
        
        if not batch_df.isEmpty():
            batch_df.write \
                .format("mongodb") \
                .mode("append") \
                .save() # Cấu hình .config() ở SparkSession sẽ được dùng
            print(f"--- [Mongo Sink] Đã ghi vào collection '{MONGO_COLLECTION_NAME}' ---")
        else:
            print(f"--- [Mongo Sink] Không có dữ liệu mới trong epoch này ---")

    query_mongo = df_windowed_counts.writeStream \
        .outputMode("update") \
        .foreachBatch(write_agg_to_mongo) \
        .trigger(processingTime="30 seconds") \
        .option("checkpointLocation", "/opt/spark/work-dir/checkpoints/mongo_agg_sink") \
        .start()


    print("=== Ứng dụng Spark Streaming đang chạy (Join + Aggregation) ===")
    print(f"=== Dữ liệu sẽ được in ra console VÀ ghi vào MongoDB (Collection: {MONGO_COLLECTION_NAME}) ===")
    
    # Đợi 1 query bất kỳ (ví dụ query_console)
    query_console.awaitTermination()

if __name__ == "__main__":
    main()

