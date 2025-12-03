"""
Simple Streaming Job for Testing
=================================
Reads events from Kafka and writes directly to MongoDB.
No complex processing - just for testing the data pipeline.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp
from app.utils.spark_factory import SparkSessionFactory
from app.connectors.kafka_connector import KafkaConnector
from app.connectors.mongodb_connector import MongoDBConnector
from app.models.event_schema import EventSchema
from app.config.settings import settings
from app.config.kafka_config import KafkaConfig
from app.config.mongodb_config import MongoDBConfig


class SimpleStreamingJob:
    """Simple streaming job - read from Kafka, write to MongoDB"""
    
    def __init__(self):
        # Create Spark session
        self.spark = SparkSessionFactory.create_streaming_session(
            "SimpleStreamingTest"
        )
        
        # Initialize configurations
        self.kafka_config = KafkaConfig(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            topic=settings.KAFKA_TOPIC
        )
        
        self.mongo_config = MongoDBConfig(
            uri=settings.MONGODB_URI,
            database=settings.MONGODB_DATABASE
        )
        
        # Initialize connectors
        self.kafka_connector = KafkaConnector(self.spark, self.kafka_config)
        self.mongo_connector = MongoDBConnector(self.spark, self.mongo_config)
        
    def run(self):
        """Execute the simple streaming pipeline"""
        print("=" * 80)
        print("🚀 Starting Simple Streaming Job (Testing)")
        print("=" * 80)
        
        # Step 1: Read from Kafka
        df_kafka = self.kafka_connector.read_stream()
        print("✓ Connected to Kafka topic:", self.kafka_config.topic)
        
        # Step 2: Parse Kafka events
        event_schema = EventSchema.get_kafka_event_schema()
        df_parsed = df_kafka.select(
            from_json(col("value").cast("string"), event_schema).alias("event"),
            current_timestamp().alias("processing_time")
        ).select("event.*", "processing_time")
        
        print("✓ Event parsing configured")
        
        # Step 3: Write to MongoDB
        query = self.mongo_connector.write_stream(
            df_parsed,
            collection="raw_events",
            checkpoint_location=settings.get_checkpoint_path("raw_events"),
            output_mode="append"
        )
        
        print("\n" + "=" * 80)
        print("✅ Streaming query started successfully!")
        print("=" * 80)
        print("\n📈 Monitoring stream... (Press Ctrl+C to stop)")
        print(f"\nWriting to MongoDB collection: raw_events")
        print("\n" + "=" * 80)
        
        # Wait for stream
        try:
            query.awaitTermination()
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping streaming query...")
            self.spark.stop()
            print("✅ Graceful shutdown complete")


def main():
    """Main entry point"""
    job = SimpleStreamingJob()
    job.run()


if __name__ == "__main__":
    main()
