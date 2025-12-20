import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, window, count
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, TimestampType

# Load environment variables from config/.env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVER = os.getenv('KAFKA_INTERNAL_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'customer_events')
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.getenv('MONGODB_DATABASE', 'bigdata_db')
MONGO_COLLECTION_NAME = "event_counts_by_category"
HDFS_NAMENODE = os.getenv('HDFS_NAMENODE', 'hdfs://localhost:9000')

def load_product_catalog(spark):
    """Load product catalog from HDFS or local"""
    hdfs_path = f"{HDFS_NAMENODE}/data/catalog/product_catalog.csv"
    local_path = "data/catalog/product_catalog.csv"
    
    try:
        print(f"📖 Loading product catalog from HDFS: {hdfs_path}")
        df = spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(hdfs_path)
        print(f"✅ Loaded {df.count()} products from HDFS")
        return df
    except Exception as e:
        print(f"⚠️  HDFS load failed: {e}")
        try:
            print(f"⏮️  Falling back to local: {local_path}")
            df = spark.read \
                .option("header", "true") \
                .option("inferSchema", "true") \
                .csv(local_path)
            print(f"✅ Loaded {df.count()} products from local")
            return df
        except Exception as e2:
            print(f"❌ Failed to load product catalog: {e2}")
            return None

def main():
    print("🚀 Initializing Spark Session...")
    
    spark = SparkSession.builder \
        .appName("CustomerJourneyStreamingK8s") \
        .master("local[*]") \
        .config("spark.mongodb.write.connection.uri", MONGO_URI) \
        .config("spark.mongodb.write.database", MONGO_DB_NAME) \
        .config("spark.mongodb.write.collection", MONGO_COLLECTION_NAME) \
        .config("spark.hadoop.fs.defaultFS", HDFS_NAMENODE) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    print("✅ Spark Session ready")

    # Load product catalog
    df_product_catalog = load_product_catalog(spark)

    # 1. Read stream from Kafka
    df_kafka = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    # 2. Define schema
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

    # 3. Parse and transform
    df_events = df_kafka.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    df_processed = df_events \
        .withColumn("event_timestamp", col("event_time").cast(TimestampType())) \
        .drop("event_time")

    df_with_watermark = df_processed \
        .withWatermark("event_timestamp", "10 minutes")

    # 4. Join with product catalog (Stream-Static Join)
    print("🔗 Joining stream with product catalog...")
    df_enriched = df_with_watermark.join(
        df_product_catalog,
        "product_id",
        "left_outer"
    )

    # 5. Complex aggregations
    print("📊 Creating windowed aggregations...")
    df_windowed_counts = df_enriched \
        .groupBy(
            window(col("event_timestamp"), "1 minute", "30 seconds").alias("time_window"),
            col("category_name"),
            col("event_type")
        ) \
        .agg(
            count("*").alias("event_count")
        )

    # 6. Write to console and MongoDB
    def write_agg_to_mongo(batch_df, epoch_id):
        print(f"--- [Mongo] Epoch {epoch_id} ---")
        
        if not batch_df.isEmpty():
            batch_df.write \
                .format("mongodb") \
                .mode("append") \
                .save()
            print(f"--- [Mongo] Wrote {batch_df.count()} aggregations ---")
        else:
            print(f"--- [Mongo] No data in this epoch ---")

    query_console = df_windowed_counts.writeStream \
        .outputMode("complete") \
        .format("console") \
        .option("truncate", "false") \
        .trigger(processingTime="30 seconds") \
        .start()

    query_mongo = df_windowed_counts.writeStream \
        .outputMode("update") \
        .foreachBatch(write_agg_to_mongo) \
        .trigger(processingTime="30 seconds") \
        .option("checkpointLocation", "./checkpoints/k8s_agg") \
        .start()

    print("=" * 60)
    print("🎯 K8s Streaming App Running (Join + Aggregation)")
    print("=" * 60)
    
    query_console.awaitTermination()

if __name__ == "__main__":
    main()