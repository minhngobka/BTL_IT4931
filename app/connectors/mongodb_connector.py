"""MongoDB connector for reading/writing data"""

from pyspark.sql import SparkSession, DataFrame
from app.config.mongodb_config import MongoDBConfig


class MongoDBConnector:
    """Handle MongoDB connections for batch and streaming"""
    
    def __init__(self, spark: SparkSession, config: MongoDBConfig):
        self.spark = spark
        self.config = config
    
    def read_collection(self, collection: str) -> DataFrame:
        """Read data from MongoDB collection"""
        df = self.spark.read \
            .format("mongodb") \
            .option("connection.uri", self.config.uri) \
            .option("database", self.config.database) \
            .option("collection", collection) \
            .load()
        
        return df
    
    def write_batch(self, df: DataFrame, collection: str, mode: str = "append") -> None:
        """Write DataFrame to MongoDB in batch mode"""
        df.write \
            .format("mongodb") \
            .option("connection.uri", self.config.uri) \
            .option("database", self.config.database) \
            .option("collection", collection) \
            .mode(mode) \
            .save()
    
    def write_stream(self, df: DataFrame, collection: str, 
                     checkpoint_location: str, output_mode: str = "append"):
        """Write streaming DataFrame to MongoDB"""
        query = df.writeStream \
            .format("mongodb") \
            .option("connection.uri", self.config.uri) \
            .option("database", self.config.database) \
            .option("collection", collection) \
            .option("checkpointLocation", checkpoint_location) \
            .outputMode(output_mode) \
            .start()
        
        return query
    
    def get_collection_count(self, collection: str) -> int:
        """Get document count for a collection"""
        df = self.read_collection(collection)
        return df.count()
