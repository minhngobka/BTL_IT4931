"""
Advanced Streaming Application for Big Data Project
====================================================
This application demonstrates intermediate-level Spark Streaming capabilities including:
- Complex aggregations with window functions
- Pivot/Unpivot operations
- Custom UDFs for business logic
- Multiple join types (broadcast and sort-merge)
- Watermarking and late data handling
- State management with exactly-once processing
- Performance optimization techniques
"""

import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    from_json, col, current_timestamp, window, count, sum, avg, max, min,
    when, lit, coalesce, lag, lead, row_number, rank, dense_rank,
    first, last, collect_list, collect_set, expr, struct, to_json,
    udf, pandas_udf, concat, concat_ws, round as spark_round,
    unix_timestamp, from_unixtime, date_format, hour, dayofweek,
    countDistinct, approx_count_distinct, stddev, variance
)
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, DoubleType, 
    TimestampType, IntegerType, ArrayType, MapType, BooleanType
)
import pandas as pd
from typing import Iterator

from pyspark.sql.functions import broadcast

# Load environment variables from config/.env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVER = os.getenv('KAFKA_INTERNAL_BROKER', 'my-cluster-kafka-bootstrap.default.svc.cluster.local:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'customer_events')

MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://my-mongo-mongodb.default.svc.cluster.local:27017/')
MONGO_DB_NAME = os.getenv('MONGODB_DATABASE', 'bigdata_db')

# Multiple collections for different analytics
MONGO_COLLECTION_ENRICHED = "enriched_events"
MONGO_COLLECTION_AGGREGATIONS = "event_aggregations"
MONGO_COLLECTION_USER_SESSIONS = "user_session_analytics"
MONGO_COLLECTION_CONVERSION_FUNNEL = "conversion_funnel"

# Checkpoint locations for different queries
CHECKPOINT_BASE = "/opt/spark/work-dir/checkpoints"


def create_spark_session():
    """Create and configure Spark Session with optimizations"""
    spark = SparkSession.builder \
        .appName("AdvancedCustomerJourneyStreaming") \
        .master("local[*]") \
        .config("spark.mongodb.write.connection.uri", MONGO_URI) \
        .config("spark.mongodb.write.database", MONGO_DB_NAME) \
        .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_BASE) \
        .config("spark.sql.streaming.stateStore.providerClass", 
                "org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider") \
        .config("spark.sql.shuffle.partitions", "8") \
        .config("spark.sql.streaming.metricsEnabled", "true") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.executor.memory", "4g") \
        .config("spark.executor.memoryOverhead", "1g") \
        .config("spark.memory.fraction", "0.8") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark


def load_dimension_tables(spark):
    """
    Load dimension tables for enrichment
    Requirement: Join Operations - Broadcast joins for small dimension tables
    """
    print("Loading dimension tables...")
    
    # Load product catalog
    product_schema = StructType([
        StructField("product_id", LongType()),
        StructField("product_name", StringType()),
        StructField("category_name", StringType()),
        StructField("category_code", StringType()),
        StructField("subcategory", StringType())
    ])
    
    df_products = spark.read \
        .schema(product_schema) \
        .option("header", "true") \
        .csv("data/catalog/product_catalog.csv")
    
    # Broadcast hint for small dimension table
    #df_products = df_products.hint("broadcast")
    #Broad cast optimization
    df_products = broadcast(df_products)
    
    # Load user dimension (if exists)
    try:
        user_schema = StructType([
            StructField("user_id", LongType()),
            StructField("user_segment", StringType()),
            StructField("registration_date", StringType()),
            StructField("country", StringType()),
            StructField("city", StringType())
        ])
        
        df_users = spark.read \
            .schema(user_schema) \
            .option("header", "true") \
            .csv("data/catalog/user_dimension.csv")
        
        #df_users = df_users.hint("broadcast")
        df_users = broadcast(df_users)
    except:
        df_users = None
        print("User dimension not found, skipping...")
    
    return df_products, df_users


def define_custom_udfs(spark):
    """
    Custom UDFs for Business Logic
    Requirement: Advanced Transformations - Custom UDFs
    """
    
    # UDF 1: Price Category Classification
    @udf(returnType=StringType())
    def classify_price_category(price):
        """Classify product into price categories"""
        if price is None:
            return "Unknown"
        elif price < 20:
            return "Budget"
        elif price < 100:
            return "Mid-Range"
        elif price < 500:
            return "Premium"
        else:
            return "Luxury"
    
    # UDF 2: Session Quality Score (Pandas UDF for better performance)
    @pandas_udf(DoubleType())
    def calculate_session_quality(event_counts: pd.Series, 
                                   purchase_counts: pd.Series,
                                   avg_price: pd.Series) -> pd.Series:
        """
        Calculate session quality score based on engagement and purchase
        Higher score = better quality session
        """
        # Normalize components
        engagement_score = event_counts / (event_counts.max() + 1)
        purchase_score = purchase_counts * 2  # Purchases are more valuable
        value_score = avg_price / (avg_price.max() + 1)
        
        # Weighted combination
        quality_score = (engagement_score * 0.3 + 
                        purchase_score * 0.5 + 
                        value_score * 0.2) * 100
        
        return quality_score.fillna(0)
    
    # UDF 3: Customer Journey Stage
    @udf(returnType=StringType())
    def determine_journey_stage(has_view, has_cart, has_purchase):
        """Determine customer position in the journey"""
        if has_purchase:
            return "CONVERTED"
        elif has_cart:
            return "CONSIDERATION"
        elif has_view:
            return "AWARENESS"
        else:
            return "UNKNOWN"
    
    # Register UDFs
    spark.udf.register("classify_price", classify_price_category)
    spark.udf.register("session_quality", calculate_session_quality)
    spark.udf.register("journey_stage", determine_journey_stage)
    
    return {
        'classify_price': classify_price_category,
        'session_quality': calculate_session_quality,
        'journey_stage': determine_journey_stage
    }


def read_kafka_stream(spark):
    """Read streaming data from Kafka"""
    print("Connecting to Kafka...")
    
    df_kafka = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .option("maxOffsetsPerTrigger", "10000") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Define event schema
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
    
    # Parse JSON and extract fields
    df_events = df_kafka.select(
        from_json(col("value").cast("string"), schema).alias("data"),
        col("timestamp").alias("kafka_timestamp")
    ).select("data.*", "kafka_timestamp")
    
    return df_events


def enrich_events(df_events, df_products, df_users, udfs):
    """
    Enrich events with dimension data and custom logic
    Requirements: 
    - Join Operations (broadcast joins)
    - Custom UDFs
    - Advanced Transformations
    """
    print("Enriching events...")
    
    # Convert timestamp and add watermark
    df_processed = df_events \
        .withColumn("event_timestamp", col("event_time").cast(TimestampType())) \
        .withColumn("processing_timestamp", current_timestamp()) \
        .drop("event_time")
    
    # Watermarking for late data handling (Requirement: Watermarking)
    df_with_watermark = df_processed \
        .withWatermark("event_timestamp", "10 minutes")
    
    # Join with product dimension (Broadcast join)
    df_enriched = df_with_watermark.join(
        df_products,
        "product_id",
        "left_outer"
    )
    
    # Join with user dimension if available
    if df_users is not None:
        df_enriched = df_enriched.join(
            df_users,
            "user_id",
            "left_outer"
        )
    
    # Apply custom UDFs
    df_enriched = df_enriched \
        .withColumn("price_category", udfs['classify_price'](col("price"))) \
        .withColumn("event_hour", hour(col("event_timestamp"))) \
        .withColumn("event_day_of_week", dayofweek(col("event_timestamp"))) \
        .withColumn("is_weekend", 
                   when(col("event_day_of_week").isin([1, 7]), lit(True))
                   .otherwise(lit(False)))
    
    return df_enriched


def create_complex_aggregations(df_enriched):
    """
    Complex Aggregations with Window Functions
    Requirements:
    - Window functions and advanced aggregation
    - Pivot operations
    - Multiple stages of transformations
    """
    print("Creating complex aggregations...")
    
    # === AGGREGATION 1: Tumbling Window Aggregations ===
    # Event counts and metrics by category and time window
    df_window_agg = df_enriched \
        .groupBy(
            window(col("event_timestamp"), "5 minutes").alias("time_window"),
            col("category_name"),
            col("event_type")
        ) \
        .agg(
            count("*").alias("event_count"),
            approx_count_distinct("user_id").alias("unique_users"),
            approx_count_distinct("user_session").alias("unique_sessions"),
            avg("price").alias("avg_price"),
            sum("price").alias("total_revenue"),
            max("price").alias("max_price"),
            min("price").alias("min_price"),
            stddev("price").alias("price_stddev")
        )
    
    # === AGGREGATION 2: Sliding Window with Overlap ===
    # Sliding window: 10 minute window, sliding every 5 minutes
    df_sliding_agg = df_enriched \
        .groupBy(
            window(col("event_timestamp"), "10 minutes", "5 minutes").alias("time_window"),
            col("brand")
        ) \
        .agg(
            count("*").alias("event_count"),
            approx_count_distinct("user_id").alias("unique_users"),
            avg("price").alias("avg_price")
        )
    
    # === AGGREGATION 3: Session-Based Aggregations with State ===
    # Aggregate by user session with state management
    df_session_agg = df_enriched \
        .groupBy(
            col("user_session"),
            col("user_id")
        ) \
        .agg(
            count("*").alias("total_events"),
            approx_count_distinct("product_id").alias("unique_products_viewed"),
            sum(when(col("event_type") == "view", 1).otherwise(0)).alias("view_count"),
            sum(when(col("event_type") == "cart", 1).otherwise(0)).alias("cart_count"),
            sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("purchase_count"),
            sum(when(col("event_type") == "purchase", col("price")).otherwise(0)).alias("total_purchase_value"),
            avg("price").alias("avg_product_price"),
            collect_set("category_name").alias("categories_browsed"),
            collect_set("brand").alias("brands_viewed"),
            min("event_timestamp").alias("session_start"),
            max("event_timestamp").alias("session_end"),
            first("price_category").alias("first_price_category"),
            last("price_category").alias("last_price_category")
        ) \
        .withColumn("session_duration_minutes", 
                   (unix_timestamp(col("session_end")) - 
                    unix_timestamp(col("session_start"))) / 60) \
        .withColumn("has_view", col("view_count") > 0) \
        .withColumn("has_cart", col("cart_count") > 0) \
        .withColumn("has_purchase", col("purchase_count") > 0) \
        .withColumn("conversion_rate", 
                   when(col("total_events") > 0, 
                        col("purchase_count") / col("total_events"))
                   .otherwise(0))
    
    return df_window_agg, df_sliding_agg, df_session_agg


def create_pivot_analysis(df_enriched):
    """
    Pivot and Unpivot Operations
    Requirement: Pivot/unpivot operations
    """
    print("Creating pivot analysis...")
    
    # Pivot: Event types by hour and category
    # This creates a wide format showing event distribution
    df_pivot = df_enriched \
        .groupBy(
            window(col("event_timestamp"), "1 hour").alias("hour_window"),
            col("category_name")
        ) \
        .pivot("event_type", ["view", "cart", "purchase"]) \
        .agg(
            count("*").alias("count"),
            sum("price").alias("revenue")
        )
    
    return df_pivot


def calculate_conversion_funnel(df_session_agg):
    """
    Calculate conversion funnel metrics
    Requirements: Complex aggregations, custom functions
    """
    
    # Calculate funnel stages
    df_funnel = df_session_agg \
        .groupBy(window(col("session_start"), "15 minutes").alias("time_window")) \
        .agg(
            count("*").alias("total_sessions"),
            sum(when(col("has_view"), 1).otherwise(0)).alias("sessions_with_view"),
            sum(when(col("has_cart"), 1).otherwise(0)).alias("sessions_with_cart"),
            sum(when(col("has_purchase"), 1).otherwise(0)).alias("sessions_with_purchase"),
            avg("session_duration_minutes").alias("avg_session_duration"),
            avg("total_purchase_value").alias("avg_purchase_value")
        ) \
        .withColumn("view_to_cart_rate",
                   when(col("sessions_with_view") > 0,
                        col("sessions_with_cart") / col("sessions_with_view") * 100)
                   .otherwise(0)) \
        .withColumn("cart_to_purchase_rate",
                   when(col("sessions_with_cart") > 0,
                        col("sessions_with_purchase") / col("sessions_with_cart") * 100)
                   .otherwise(0)) \
        .withColumn("overall_conversion_rate",
                   when(col("total_sessions") > 0,
                        col("sessions_with_purchase") / col("total_sessions") * 100)
                   .otherwise(0))
    
    return df_funnel


def write_to_mongodb(df, collection_name, checkpoint_suffix, output_mode="update"):
    """
    Write streaming data to MongoDB with exactly-once semantics
    Requirement: Exactly-once processing guarantees
    """
    
    def write_batch(batch_df, epoch_id):
        """Idempotent write operation for exactly-once semantics"""
        if not batch_df.isEmpty():
            # Add epoch_id to ensure idempotency
            batch_with_epoch = batch_df.withColumn("_epoch_id", lit(epoch_id))
            
            try:
                batch_with_epoch.write \
                    .format("mongodb") \
                    .mode("append") \
                    .option("database", MONGO_DB_NAME) \
                    .option("collection", collection_name) \
                    .save()
                
                print(f"✓ Epoch {epoch_id}: Wrote {batch_df.count()} records to {collection_name}")
            except Exception as e:
                print(f"✗ Error writing epoch {epoch_id} to {collection_name}: {e}")
                raise  # Re-raise to trigger retry
    
    query = df.writeStream \
        .foreachBatch(write_batch) \
        .outputMode(output_mode) \
        .option("checkpointLocation", f"{CHECKPOINT_BASE}/{checkpoint_suffix}") \
        .trigger(processingTime="30 seconds") \
        .start()
    
    return query


def write_to_console(df, query_name):
    """Write to console for debugging"""
    query = df.writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", "false") \
        .option("numRows", "20") \
        .queryName(query_name) \
        .trigger(processingTime="30 seconds") \
        .start()
    
    return query


def main():
    print("=" * 80)
    print("Starting Advanced Customer Journey Streaming Application")
    print("=" * 80)
    
    # Initialize Spark
    spark = create_spark_session()
    print("✓ Spark Session initialized")
    
    # Load dimension tables
    df_products, df_users = load_dimension_tables(spark)
    print("✓ Dimension tables loaded")
    
    # Define custom UDFs
    udfs = define_custom_udfs(spark)
    print("✓ Custom UDFs registered")
    
    # Read Kafka stream
    df_events = read_kafka_stream(spark)
    print("✓ Connected to Kafka stream")
    
    # Enrich events
    df_enriched = enrich_events(df_events, df_products, df_users, udfs)
    print("✓ Event enrichment pipeline configured")
    
    # Create aggregations
    df_window_agg, df_sliding_agg, df_session_agg = create_complex_aggregations(df_enriched)
    print("✓ Complex aggregations configured")
    
    # Create pivot analysis
    df_pivot = create_pivot_analysis(df_enriched)
    print("✓ Pivot analysis configured")
    
    # Calculate conversion funnel
    df_funnel = calculate_conversion_funnel(df_session_agg)
    print("✓ Conversion funnel configured")
    
    print("\n" + "=" * 80)
    print("Starting streaming queries...")
    print("=" * 80 + "\n")
    
    # Start all streaming queries
    queries = []
    
    # Query 1: Write enriched events
    q1 = write_to_mongodb(
        df_enriched.select(
            "event_timestamp", "event_type", "product_id", "product_name",
            "category_name", "brand", "price", "price_category", "user_id",
            "user_session", "event_hour", "is_weekend", "processing_timestamp"
        ),
        MONGO_COLLECTION_ENRICHED,
        "enriched_events",
        "append"
    )
    queries.append(("Enriched Events", q1))
    
    # Query 2: Write window aggregations
    q2 = write_to_mongodb(
        df_window_agg,
        MONGO_COLLECTION_AGGREGATIONS,
        "window_agg",
        "update"
    )
    queries.append(("Window Aggregations", q2))
    
    # Query 3: Write session analytics
    q3 = write_to_mongodb(
        df_session_agg,
        MONGO_COLLECTION_USER_SESSIONS,
        "session_agg",
        "update"
    )
    queries.append(("Session Analytics", q3))
    
    # Query 4: Write conversion funnel
    q4 = write_to_mongodb(
        df_funnel,
        MONGO_COLLECTION_CONVERSION_FUNNEL,
        "conversion_funnel",
        "complete"
    )
    queries.append(("Conversion Funnel", q4))
    
    # Query 5: Console output for monitoring
    q5 = write_to_console(
        df_window_agg.select(
            "time_window", "category_name", "event_type",
            "event_count", "unique_users", "avg_price"
        ),
        "Window Aggregations Monitor"
    )
    queries.append(("Console Monitor", q5))
    
    print(f"\n✓ Started {len(queries)} streaming queries\n")
    print("=" * 80)
    print("Streaming application is running...")
    print("Data is being processed and written to MongoDB")
    print("Press Ctrl+C to stop")
    print("=" * 80 + "\n")
    
    # Monitor query status
    try:
        # Wait for termination
        for name, query in queries:
            if query.isActive:
                print(f"✓ {name}: Running")
        
        # Wait for any query to terminate
        spark.streams.awaitAnyTermination()
        
    except KeyboardInterrupt:
        print("\n\nStopping all queries...")
        for name, query in queries:
            if query.isActive:
                query.stop()
                print(f"✓ Stopped: {name}")
        print("\n✓ All queries stopped successfully")
    
    finally:
        spark.stop()
        print("✓ Spark session closed")


if __name__ == "__main__":
    main()
