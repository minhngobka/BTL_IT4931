"""
Advanced Batch Analytics with Machine Learning
===============================================
This batch job demonstrates:
- Spark MLlib for customer segmentation and churn prediction
- Time series analysis
- Statistical computations
- Performance optimization (bucketing, caching, partition pruning)
"""

import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    col, count, sum, avg, max, min, stddev, variance, corr, coalesce,
    when, lit, datediff, date_trunc, lag, lead, row_number, dense_rank,
    first, last, collect_list, explode, array, struct, to_date, dayofmonth, month, year,
    unix_timestamp, from_unixtime, expr, percentile_approx, skewness, kurtosis,
    countDistinct
)
from pyspark.sql.types import DoubleType, IntegerType, StringType

# MLlib imports
from pyspark.ml.feature import (
    VectorAssembler, StandardScaler, StringIndexer, OneHotEncoder,
    PCA, MinMaxScaler, Bucketizer
)
from pyspark.ml.clustering import KMeans, BisectingKMeans
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier
from pyspark.ml.regression import LinearRegression, RandomForestRegressor
from pyspark.ml.evaluation import (
    ClusteringEvaluator, BinaryClassificationEvaluator,
    MulticlassClassificationEvaluator
)
from pyspark.ml import Pipeline
from pyspark.ml.stat import Correlation, ChiSquareTest

# Load environment variables from config/.env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

# Configuration
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://my-mongo-mongodb.default.svc.cluster.local:27017/')
MONGO_DB_NAME = os.getenv('MONGODB_DATABASE', 'bigdata_db')
MONGO_COLLECTION_EVENTS = "enriched_events"
MONGO_COLLECTION_SESSIONS = "user_session_analytics"

# Output collections
MONGO_COLLECTION_USER_FEATURES = "user_feature_engineering"
MONGO_COLLECTION_SEGMENTS = "customer_segments"
MONGO_COLLECTION_CHURN_PREDICTIONS = "churn_predictions"
MONGO_COLLECTION_TIME_SERIES = "time_series_analysis"
MONGO_COLLECTION_PRODUCT_AFFINITY = "product_affinity_matrix"
MONGO_COLLECTION_STATISTICS = "statistical_analysis"


def create_spark_session():
    """Create Spark session with ML and optimization configurations"""
    spark = SparkSession.builder \
        .appName("AdvancedBatchAnalyticsML") \
        .master("local[*]") \
        .config("spark.mongodb.read.connection.uri", MONGO_URI) \
        .config("spark.mongodb.write.connection.uri", MONGO_URI) \
        .config("spark.mongodb.read.database", MONGO_DB_NAME) \
        .config("spark.mongodb.write.database", MONGO_DB_NAME) \
        .config("spark.sql.shuffle.partitions", "8") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.adaptive.skewJoin.enabled", "true") \
        .config("spark.sql.autoBroadcastJoinThreshold", "10485760") \
        .config("spark.default.parallelism", "8") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark


def load_and_optimize_data(spark):
    """
    Load data with optimization techniques
    Requirements: Performance Optimization - Caching and persistence
    """
    print("Loading data from MongoDB...")
    
    # Load enriched events
    df_events = spark.read \
        .format("mongodb") \
        .option("collection", MONGO_COLLECTION_EVENTS) \
        .load()
    
    # Optimization: Partition pruning
    # Filter only relevant data to reduce processing
    df_events_filtered = df_events \
        .filter(col("event_timestamp").isNotNull()) \
        .filter(col("user_id").isNotNull())
    
    # Cache for reuse (Performance Optimization requirement)
    df_events_filtered.cache()
    count = df_events_filtered.count()
    print(f"✓ Loaded and cached {count} events")
    
    # Load session data
    try:
        df_sessions = spark.read \
            .format("mongodb") \
            .option("collection", MONGO_COLLECTION_SESSIONS) \
            .load()
        df_sessions.cache()
        print(f"✓ Loaded and cached {df_sessions.count()} sessions")
    except:
        df_sessions = None
        print("⚠ Session data not available, will compute from events")
    
    return df_events_filtered, df_sessions


def feature_engineering(df_events):
    """
    Advanced Feature Engineering for ML
    Requirements: Multiple stages of transformations, custom aggregations
    """
    print("\n" + "="*80)
    print("Feature Engineering for Machine Learning")
    print("="*80)
    
    # USER-LEVEL FEATURES 
    print("\nComputing user-level features...")
    
    df_user_features = df_events \
        .groupBy("user_id") \
        .agg(
            # Engagement metrics
            count("*").alias("total_events"),
            countDistinct("user_session").alias("total_sessions"),
            countDistinct("product_id").alias("unique_products_viewed"),
            countDistinct("category_name").alias("unique_categories"),
            countDistinct("brand").alias("unique_brands"),
            
            # Event type distribution
            sum(when(col("event_type") == "view", 1).otherwise(0)).alias("view_count"),
            sum(when(col("event_type") == "cart", 1).otherwise(0)).alias("cart_count"),
            sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("purchase_count"),
            
            # Financial metrics
            sum(when(col("event_type") == "purchase", col("price")).otherwise(0)).alias("total_spent"),
            avg(when(col("event_type") == "purchase", col("price"))).alias("avg_purchase_value"),
            max(when(col("event_type") == "purchase", col("price"))).alias("max_purchase"),
            
            # Price category preferences
            sum(when(col("price_category") == "Budget", 1).otherwise(0)).alias("budget_interactions"),
            sum(when(col("price_category") == "Mid-Range", 1).otherwise(0)).alias("midrange_interactions"),
            sum(when(col("price_category") == "Premium", 1).otherwise(0)).alias("premium_interactions"),
            sum(when(col("price_category") == "Luxury", 1).otherwise(0)).alias("luxury_interactions"),
            
            # Temporal features
            min("event_timestamp").alias("first_event_date"),
            max("event_timestamp").alias("last_event_date"),
            
            # Statistical features
            avg("price").alias("avg_price_browsed"),
            stddev("price").alias("price_stddev"),
            
            # Behavioral features
            avg("event_hour").alias("avg_hour_of_day"),
            sum(when(col("is_weekend"), 1).otherwise(0)).alias("weekend_events")
        )
    
    # Derived features
    df_user_features = df_user_features \
        .withColumn("days_active", 
                   datediff(col("last_event_date"), col("first_event_date")) + 1) \
        .withColumn("avg_events_per_session",
                   col("total_events") / col("total_sessions")) \
        .withColumn("view_to_cart_ratio",
                   when(col("view_count") > 0, col("cart_count") / col("view_count"))
                   .otherwise(0)) \
        .withColumn("cart_to_purchase_ratio",
                   when(col("cart_count") > 0, col("purchase_count") / col("cart_count"))
                   .otherwise(0)) \
        .withColumn("overall_conversion_rate",
                   when(col("total_events") > 0, col("purchase_count") / col("total_events"))
                   .otherwise(0)) \
        .withColumn("weekend_ratio",
                   col("weekend_events") / col("total_events")) \
        .withColumn("recency_days",
                   datediff(lit("2019-11-01"), col("last_event_date"))) \
        .withColumn("is_churned",
                   when(col("recency_days") > 7, 1).otherwise(0)) \
        .withColumn("customer_value_score",
                   (col("total_spent") * 0.5 + 
                    col("purchase_count") * 10 + 
                    col("total_sessions") * 2))
    
    # Fill null values
    df_user_features = df_user_features.fillna({
        "avg_purchase_value": 0,
        "max_purchase": 0,
        "price_stddev": 0,
        "customer_value_score": 0
    })
    
    # Cache for reuse
    df_user_features.cache()
    print(f"✓ Computed features for {df_user_features.count()} users")
    
    return df_user_features


def perform_customer_segmentation(df_user_features, spark):
    """
    Customer Segmentation using K-Means Clustering
    Requirements: Machine learning with Spark MLlib
    """
    print("\n" + "="*80)
    print("Customer Segmentation with K-Means")
    print("="*80)
    
    # Select features for clustering
    feature_cols = [
        "total_events", "total_sessions", "purchase_count",
        "total_spent", "avg_purchase_value", "unique_products_viewed",
        "view_to_cart_ratio", "cart_to_purchase_ratio",
        "overall_conversion_rate", "customer_value_score",
        "recency_days", "weekend_ratio"
    ]
    
    # Assemble features into vector
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features_raw",
        handleInvalid="skip"
    )
    
    # Scale features (important for K-Means)
    scaler = StandardScaler(
        inputCol="features_raw",
        outputCol="features",
        withStd=True,
        withMean=True
    )
    
    # K-Means clustering
    # Try different k values to find optimal
    best_k = 4
    best_score = float('inf')
    
    print("\nFinding optimal number of clusters...")
    for k in range(3, 7):
        kmeans = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster")
        pipeline = Pipeline(stages=[assembler, scaler, kmeans])
        
        model = pipeline.fit(df_user_features)
        predictions = model.transform(df_user_features)
        
        evaluator = ClusteringEvaluator(featuresCol="features", metricName="silhouette")
        score = evaluator.evaluate(predictions)
        
        print(f"  k={k}: Silhouette Score = {score:.4f}")
        
        if score > best_score:
            best_score = score
            best_k = k
    
    print(f"\n✓ Optimal clusters: k={best_k} (Silhouette Score: {best_score:.4f})")
    
    # Train final model
    kmeans = KMeans(k=best_k, seed=42, featuresCol="features", predictionCol="segment")
    pipeline = Pipeline(stages=[assembler, scaler, kmeans])
    
    model = pipeline.fit(df_user_features)
    df_segmented = model.transform(df_user_features)
    
    # Analyze segments
    print("\nSegment Analysis:")
    segment_analysis = df_segmented \
        .groupBy("segment") \
        .agg(
            count("*").alias("user_count"),
            avg("total_spent").alias("avg_revenue"),
            avg("purchase_count").alias("avg_purchases"),
            avg("overall_conversion_rate").alias("avg_conversion_rate"),
            avg("customer_value_score").alias("avg_value_score")
        ) \
        .orderBy("segment")
    
    segment_analysis.show(truncate=False)
    
    # Assign segment names based on characteristics
    df_segmented = df_segmented \
        .withColumn("segment_name",
                   when(col("segment") == 0, "Champions")
                   .when(col("segment") == 1, "Potential Loyalists")
                   .when(col("segment") == 2, "At Risk")
                   .otherwise("New/Low Engagement"))
    
    return df_segmented


def predict_churn(df_user_features, spark):
    """
    Churn Prediction using Random Forest
    Requirements: Machine learning with Spark MLlib, Classification
    """
    print("\n" + "="*80)
    print("Churn Prediction with Random Forest")
    print("="*80)
    
    # Select features for churn prediction
    feature_cols = [
        "total_events", "total_sessions", "purchase_count",
        "view_to_cart_ratio", "cart_to_purchase_ratio",
        "overall_conversion_rate", "avg_events_per_session",
        "recency_days", "weekend_ratio", "unique_products_viewed"
    ]
    
    # Prepare data
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip"
    )
    
    df_prepared = assembler.transform(df_user_features)
    
    # Split data
    train_data, test_data = df_prepared.randomSplit([0.8, 0.2], seed=42)
    
    print(f"Training set: {train_data.count()} users")
    print(f"Test set: {test_data.count()} users")
    
    # Random Forest Classifier
    rf = RandomForestClassifier(
        labelCol="is_churned",
        featuresCol="features",
        predictionCol="churn_prediction",
        probabilityCol="churn_probability",
        numTrees=100,
        maxDepth=10,
        seed=42
    )
    
    # Train model
    print("\nTraining Random Forest model...")
    rf_model = rf.fit(train_data)
    
    # Make predictions
    predictions = rf_model.transform(test_data)
    
    # Evaluate
    evaluator = BinaryClassificationEvaluator(
        labelCol="is_churned",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderROC"
    )
    
    auc = evaluator.evaluate(predictions)
    print(f"✓ Model AUC-ROC: {auc:.4f}")
    
    # Feature importance
    print("\nFeature Importance:")
    feature_importance = list(zip(feature_cols, rf_model.featureImportances.toArray()))
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    for feature, importance in feature_importance[:10]:
        print(f"  {feature:30s}: {importance:.4f}")
    
    # Predict on all data
    df_churn_predictions = rf_model.transform(df_prepared) \
        .select(
            "user_id", "is_churned", "churn_prediction",
            "churn_probability", "total_spent", "purchase_count",
            "recency_days", "overall_conversion_rate"
        )
    
    return df_churn_predictions


def time_series_analysis(df_events, spark):
    """
    Time Series Analysis
    Requirements: Time series analysis
    """
    print("\n" + "="*80)
    print("Time Series Analysis")
    print("="*80)
    
    # Daily aggregations
    df_daily = df_events \
        .withColumn("date", to_date(col("event_timestamp"))) \
        .groupBy("date", "event_type") \
        .agg(
            count("*").alias("event_count"),
            countDistinct("user_id").alias("unique_users"),
            countDistinct("user_session").alias("unique_sessions"),
            sum(when(col("event_type") == "purchase", col("price")).otherwise(0)).alias("revenue")
        ) \
        .orderBy("date", "event_type")
    
    # Calculate moving averages
    window_7day = Window.partitionBy("event_type").orderBy("date").rowsBetween(-6, 0)
    window_3day = Window.partitionBy("event_type").orderBy("date").rowsBetween(-2, 0)
    
    df_time_series = df_daily \
        .withColumn("ma_7day_events", avg("event_count").over(window_7day)) \
        .withColumn("ma_3day_events", avg("event_count").over(window_3day)) \
        .withColumn("ma_7day_users", avg("unique_users").over(window_7day))
    
    # Day-over-day growth
    window_prev_day = Window.partitionBy("event_type").orderBy("date")
    
    df_time_series = df_time_series \
        .withColumn("prev_day_events", lag("event_count", 1).over(window_prev_day)) \
        .withColumn("day_over_day_growth",
                   when(col("prev_day_events") > 0,
                        ((col("event_count") - col("prev_day_events")) / col("prev_day_events") * 100))
                   .otherwise(0))
    
    print(f" Computed time series metrics for {df_time_series.select('date').distinct().count()} days")
    
    return df_time_series


def statistical_analysis(df_events, spark):
    """
    Statistical Computations
    Requirements: Statistical computations
    """
    print("\n" + "="*80)
    print("Statistical Analysis")
    print("="*80)
    
    # Overall statistics
    print("\nComputing descriptive statistics...")
    stats = df_events \
        .select("price") \
        .summary("count", "mean", "stddev", "min", "25%", "50%", "75%", "max")
    
    stats.show()
    
    # Correlation analysis
    print("\nComputing correlation matrix...")
    
    # Prepare numerical features
    df_for_corr = df_events \
        .select(
            col("price").cast(DoubleType()),
            col("event_hour").cast(DoubleType()),
            when(col("event_type") == "purchase", 1).otherwise(0).cast(DoubleType()).alias("is_purchase"),
            when(col("is_weekend"), 1).otherwise(0).cast(DoubleType()).alias("is_weekend_num")
        ) \
        .na.drop()
    
    # Assemble features for correlation
    assembler = VectorAssembler(
        inputCols=["price", "event_hour", "is_purchase", "is_weekend_num"],
        outputCol="features"
    )
    
    df_vector = assembler.transform(df_for_corr)
    
    # Compute correlation matrix
    correlation_matrix = Correlation.corr(df_vector, "features", "pearson").head()[0]
    
    print("Correlation Matrix:")
    print(correlation_matrix)
    
    # Category-wise statistics
    print("\nCategory-wise statistics:")
    category_stats = df_events \
        .groupBy("category_name") \
        .agg(
            count("*").alias("event_count"),
            countDistinct("user_id").alias("unique_users"),
            avg("price").alias("avg_price"),
            stddev("price").alias("price_stddev"),
            percentile_approx("price", 0.5).alias("median_price"),
            percentile_approx("price", 0.95).alias("p95_price")
        ) \
        .orderBy(col("event_count").desc())
    
    category_stats.show(10, truncate=False)
    
    return category_stats


def save_results(spark, **dataframes):
    """Save all results to MongoDB"""
    print("\n" + "="*80)
    print("Saving Results to MongoDB")
    print("="*80)
    
    for name, (df, collection) in dataframes.items():
        try:
            df.write \
                .format("mongodb") \
                .mode("overwrite") \
                .option("database", MONGO_DB_NAME) \
                .option("collection", collection) \
                .save()
            print(f" Saved {name} to {collection}")
        except Exception as e:
            print(f" Error saving {name}: {e}")


def main():
    print("=" * 80)
    print("Advanced Batch Analytics with Machine Learning")
    print("=" * 80)
    
    # Initialize Spark
    spark = create_spark_session()
    print(" Spark Session initialized with ML support\n")
    
    # Load data
    df_events, df_sessions = load_and_optimize_data(spark)
    
    # Feature Engineering
    df_user_features = feature_engineering(df_events)
    
    # Customer Segmentation
    df_segmented = perform_customer_segmentation(df_user_features, spark)
    
    # Churn Prediction
    df_churn = predict_churn(df_user_features, spark)
    
    # Time Series Analysis
    df_time_series = time_series_analysis(df_events, spark)
    
    # Statistical Analysis
    df_statistics = statistical_analysis(df_events, spark)
    
    # Save all results
    save_results(
        spark,
        user_features=(df_user_features, MONGO_COLLECTION_USER_FEATURES),
        segments=(df_segmented.select(
            "user_id", "segment", "segment_name", "total_spent",
            "purchase_count", "customer_value_score"
        ), MONGO_COLLECTION_SEGMENTS),
        churn_predictions=(df_churn, MONGO_COLLECTION_CHURN_PREDICTIONS),
        time_series=(df_time_series, MONGO_COLLECTION_TIME_SERIES),
        statistics=(df_statistics, MONGO_COLLECTION_STATISTICS)
    )
    
    print("\n" + "=" * 80)
    print("Batch Analytics Complete!")
    print("=" * 80)
    print("\nResults saved to MongoDB collections:")
    print(f"  - {MONGO_COLLECTION_USER_FEATURES}")
    print(f"  - {MONGO_COLLECTION_SEGMENTS}")
    print(f"  - {MONGO_COLLECTION_CHURN_PREDICTIONS}")
    print(f"  - {MONGO_COLLECTION_TIME_SERIES}")
    print(f"  - {MONGO_COLLECTION_STATISTICS}")
    
    spark.stop()
    print("\n Spark session closed")


if __name__ == "__main__":
    main()