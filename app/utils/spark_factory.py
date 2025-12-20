"""Spark session factory"""

from pyspark.sql import SparkSession
from app.config.settings import settings
from app.config.spark_config import SparkConfig
from app.config.mongodb_config import MongoDBConfig


class SparkSessionFactory:
    """Factory for creating configured Spark sessions"""
    
    @staticmethod
    def create_session(app_name: str, spark_config: SparkConfig = None, 
                      mongo_config: MongoDBConfig = None) -> SparkSession:
        """
        Create and configure a Spark session
        
        Args:
            app_name: Application name
            spark_config: Spark configuration (optional)
            mongo_config: MongoDB configuration (optional)
        
        Returns:
            Configured SparkSession
        """
        if spark_config is None:
            spark_config = SparkConfig(app_name=app_name)
        
        builder = SparkSession.builder.appName(app_name)
        
        # Apply Spark configuration
        for key, value in spark_config.get_spark_conf().items():
            builder = builder.config(key, value)
        
        # Apply MongoDB configuration if provided
        if mongo_config:
            builder = builder.config("spark.mongodb.write.connection.uri", mongo_config.uri)
            builder = builder.config("spark.mongodb.write.database", mongo_config.database)
            builder = builder.config("spark.mongodb.read.connection.uri", mongo_config.uri)
            builder = builder.config("spark.mongodb.read.database", mongo_config.database)
        
        spark = builder.getOrCreate()
        spark.sparkContext.setLogLevel("WARN")
        
        return spark
    
    @staticmethod
    def create_streaming_session(app_name: str) -> SparkSession:
        """Create a Spark session optimized for streaming"""
        spark_config = SparkConfig(
            app_name=app_name,
            master=settings.SPARK_MASTER,
            checkpoint_location=settings.CHECKPOINT_BASE
        )
        
        mongo_config = MongoDBConfig(
            uri=settings.MONGODB_URI,
            database=settings.MONGODB_DATABASE
        )
        
        return SparkSessionFactory.create_session(app_name, spark_config, mongo_config)
    
    @staticmethod
    def create_batch_session(app_name: str) -> SparkSession:
        """Create a Spark session optimized for batch processing"""
        spark_config = SparkConfig(
            app_name=app_name,
            master=settings.SPARK_MASTER,
            shuffle_partitions=16,  # More partitions for batch
            default_parallelism=16
        )
        
        mongo_config = MongoDBConfig(
            uri=settings.MONGODB_URI,
            database=settings.MONGODB_DATABASE
        )
        
        return SparkSessionFactory.create_session(app_name, spark_config, mongo_config)
