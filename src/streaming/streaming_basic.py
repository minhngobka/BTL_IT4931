import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, TimestampType

# Load environment variables from config/.env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVER = os.getenv('KAFKA_INTERNAL_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'customer_events')
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.getenv('MONGODB_DATABASE', 'bigdata_db')
MONGO_COLLECTION_NAME = "customer_events"
SPARK_CHECKPOINT_DIR = os.getenv('SPARK_CHECKPOINT_DIR', './checkpoints')
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
        .appName("CustomerJourneyStreaming") \
        .master("local[*]") \
        .config("spark.mongodb.output.uri", f"{MONGO_URI}{MONGO_DB_NAME}.{MONGO_COLLECTION_NAME}") \
        .config("spark.hadoop.fs.defaultFS", HDFS_NAMENODE) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    print("✅ Spark Session ready")

    # Load product catalog for enrichment
    df_products = load_product_catalog(spark)

    # 1. Read stream from Kafka
    df_kafka = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    print("✅ Connected to Kafka topic. Waiting for data...")

    # 2. Define schema for event data
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

    # 3. Transform data
    df_events = df_kafka.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    df_processed = df_events \
        .withColumn("event_timestamp", col("event_time").cast(TimestampType())) \
        .withColumn("processing_timestamp", current_timestamp()) \
        .drop("event_time")

    # Apply watermarking
    df_with_watermark = df_processed \
        .withWatermark("event_timestamp", "10 minutes")

    print("✅ Schema defined and transformations applied. Starting stream...")

    # 4. Write to MongoDB
    def write_to_mongo(batch_df, epoch_id):
        print(f"--- Epoch {epoch_id} processing ---")
        if batch_df.count() == 0:
            print("--- No new data in this epoch ---")
            return

        # Write events
        batch_df.write \
            .format("mongodb") \
            .mode("append") \
            .option("uri", MONGO_URI) \
            .option("database", MONGO_DB_NAME) \
            .option("collection", MONGO_COLLECTION_NAME) \
            .save()

        print(f"--- Wrote {batch_df.count()} rows to 'customer_events' ---")

        # Update product catalog
        try:
            pdf = batch_df.select("product_id", "category_id", "brand", "price").distinct().toPandas()
            client = MongoClient(MONGO_URI)
            catalog_col = client[MONGO_DB_NAME]["product_catalog"]

            for _, row in pdf.iterrows():
                product_id = int(row["product_id"])
                name = f"Product {product_id}"
                img = f"https://picsum.photos/300/300?random={product_id}"

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
            print(f"✓ Updated product_catalog with {len(pdf)} products")
        except Exception as e:
            print(f"⚠ Error updating product_catalog: {e}")

    query = df_with_watermark.writeStream \
        .foreachBatch(write_to_mongo) \
        .outputMode("update") \
        .option("checkpointLocation", SPARK_CHECKPOINT_DIR) \
        .trigger(processingTime="15 seconds") \
        .start()

    print("=" * 60)
    print("🎯 Spark Streaming Application Running")
    print("📥 Kafka → Spark → MongoDB")
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 60)
    
    query.awaitTermination()

if __name__ == "__main__":
    main()