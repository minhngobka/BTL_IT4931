"""Kafka connector for reading/writing streams"""

from pyspark.sql import SparkSession, DataFrame
from app.config.kafka_config import KafkaConfig


class KafkaConnector:
    """Handle Kafka stream connections"""
    
    def __init__(self, spark: SparkSession, config: KafkaConfig):
        self.spark = spark
        self.config = config
    
    def read_stream(self) -> DataFrame:
        """Read streaming data from Kafka"""
        kafka_options = self.config.get_spark_kafka_options()
        
        df = self.spark.readStream \
            .format("kafka") \
            .options(**kafka_options) \
            .load()
        
        return df
    
    def write_stream(self, df: DataFrame, checkpoint_location: str) -> None:
        """Write streaming data to Kafka (for testing/debugging)"""
        query = df.writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.config.bootstrap_servers) \
            .option("topic", self.config.topic) \
            .option("checkpointLocation", checkpoint_location) \
            .start()
        
        return query
