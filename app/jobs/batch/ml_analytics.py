"""
ML Analytics Batch Job
=======================
Machine learning pipeline for customer segmentation and churn prediction
"""

from pyspark.sql.functions import col, count, sum as _sum, avg, stddev, datediff, current_date
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import ClusteringEvaluator, BinaryClassificationEvaluator
from pyspark.ml import Pipeline

from app.utils.spark_factory import SparkSessionFactory
from app.connectors.mongodb_connector import MongoDBConnector
from app.config.settings import settings
from app.config.mongodb_config import MongoDBConfig


class MLAnalyticsJob:
    """Batch machine learning analytics job"""
    
    def __init__(self):
        # Create Spark session
        self.spark = SparkSessionFactory.create_batch_session(
            "MLAnalyticsBatch"
        )
        
        # Initialize MongoDB connector
        self.mongo_config = MongoDBConfig(
            uri=settings.MONGODB_URI,
            database=settings.MONGODB_DATABASE
        )
        self.mongo_connector = MongoDBConnector(self.spark, self.mongo_config)
    
    def load_data(self):
        """Load data from MongoDB"""
        print("Loading data from MongoDB...")
        
        self.df_events = self.mongo_connector.read_collection(
            self.mongo_config.ENRICHED_EVENTS
        )
        
        # Filter and cache
        self.df_events = self.df_events \
            .filter(col("event_timestamp").isNotNull()) \
            .filter(col("user_id").isNotNull()) \
            .cache()
        
        count = self.df_events.count()
        print(f"✓ Loaded {count:,} events")
    
    def feature_engineering(self):
        """Create features for ML models"""
        print("Performing feature engineering...")
        
        # User-level aggregations
        df_user_features = self.df_events.groupBy("user_id").agg(
            count("*").alias("total_events"),
            _sum((col("event_type") == "view").cast("int")).alias("view_count"),
            _sum((col("event_type") == "cart").cast("int")).alias("cart_count"),
            _sum((col("event_type") == "purchase").cast("int")).alias("purchase_count"),
            _sum("price").alias("total_spent"),
            avg("price").alias("avg_order_value"),
            stddev("price").alias("price_stddev")
        )
        
        # Calculate conversion rates
        df_user_features = df_user_features.withColumn(
            "view_to_cart_rate",
            col("cart_count") / (col("view_count") + 1)
        ).withColumn(
            "cart_to_purchase_rate",
            col("purchase_count") / (col("cart_count") + 1)
        )
        
        # Save features
        self.mongo_connector.write_batch(
            df_user_features,
            collection=self.mongo_config.USER_FEATURES,
            mode="overwrite"
        )
        
        print(f"✓ Created features for {df_user_features.count():,} users")
        return df_user_features
    
    def customer_segmentation(self, df_features):
        """K-Means clustering for customer segmentation"""
        print("\nPerforming customer segmentation (K-Means)...")
        
        # Prepare features
        feature_cols = [
            "total_events", "view_count", "cart_count", "purchase_count",
            "total_spent", "avg_order_value"
        ]
        
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features_raw"
        )
        
        scaler = StandardScaler(
            inputCol="features_raw",
            outputCol="features"
        )
        
        kmeans = KMeans(
            featuresCol="features",
            predictionCol="segment",
            k=4,
            seed=42
        )
        
        # Create pipeline
        pipeline = Pipeline(stages=[assembler, scaler, kmeans])
        
        # Fit model
        model = pipeline.fit(df_features)
        df_segments = model.transform(df_features)
        
        # Evaluate
        evaluator = ClusteringEvaluator(
            featuresCol="features",
            predictionCol="segment",
            metricName="silhouette"
        )
        
        silhouette = evaluator.evaluate(df_segments)
        print(f"✓ Silhouette Score: {silhouette:.4f}")
        
        # Save segments
        df_output = df_segments.select("user_id", "segment")
        self.mongo_connector.write_batch(
            df_output,
            collection=self.mongo_config.CUSTOMER_SEGMENTS,
            mode="overwrite"
        )
        
        # Show segment statistics
        df_segments.groupBy("segment").agg(
            count("*").alias("user_count"),
            avg("total_spent").alias("avg_revenue"),
            avg("purchase_count").alias("avg_purchases")
        ).show()
        
        return df_segments
    
    def churn_prediction(self, df_features):
        """Random Forest for churn prediction"""
        print("\nTraining churn prediction model (Random Forest)...")
        
        # Define churn (users with no purchases in recent activity)
        df_features = df_features.withColumn(
            "is_churned",
            (col("purchase_count") == 0).cast("int")
        )
        
        # Prepare features
        feature_cols = [
            "total_events", "view_count", "cart_count",
            "view_to_cart_rate", "cart_to_purchase_rate", "avg_order_value"
        ]
        
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features",
            handleInvalid="skip"
        )
        
        rf = RandomForestClassifier(
            featuresCol="features",
            labelCol="is_churned",
            predictionCol="churn_prediction",
            probabilityCol="churn_probability",
            numTrees=50,
            maxDepth=5,
            seed=42
        )
        
        # Train-test split
        train_df, test_df = df_features.randomSplit([0.8, 0.2], seed=42)
        
        # Create and fit pipeline
        pipeline = Pipeline(stages=[assembler, rf])
        model = pipeline.fit(train_df)
        
        # Predictions
        predictions = model.transform(test_df)
        
        # Evaluate
        evaluator = BinaryClassificationEvaluator(
            labelCol="is_churned",
            rawPredictionCol="churn_prediction",
            metricName="areaUnderROC"
        )
        
        auc = evaluator.evaluate(predictions)
        print(f"✓ AUC-ROC: {auc:.4f}")
        
        # Save predictions
        df_output = predictions.select("user_id", "churn_prediction", "churn_probability")
        self.mongo_connector.write_batch(
            df_output,
            collection=self.mongo_config.CHURN_PREDICTIONS,
            mode="overwrite"
        )
        
        return predictions
    
    def run(self):
        """Execute the ML analytics job"""
        print("=" * 60)
        print("Starting ML Analytics Batch Job")
        print("=" * 60)
        
        # Load data
        self.load_data()
        
        # Feature engineering
        df_features = self.feature_engineering()
        
        # Customer segmentation
        df_segments = self.customer_segmentation(df_features)
        
        # Churn prediction
        df_predictions = self.churn_prediction(df_features)
        
        print("\n" + "=" * 60)
        print("ML Analytics Job Completed Successfully!")
        print("=" * 60)
        
        self.spark.stop()


def main():
    """Main entry point"""
    job = MLAnalyticsJob()
    job.run()


if __name__ == "__main__":
    main()
