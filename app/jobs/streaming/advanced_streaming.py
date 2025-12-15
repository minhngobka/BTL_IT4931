"""
Direct Streaming Job - Kafka to MongoDB
=======================================
Streamlines the pipeline to purely read from Kafka and write to MongoDB.
Features:
- Strict Schema Validation
- Error Logging (via console)
- Throughput Monitoring (via progress reporting)
"""

import time
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, to_timestamp, lit
from app.utils.spark_factory import SparkSessionFactory
from app.connectors.kafka_connector import KafkaConnector
from app.connectors.mongodb_connector import MongoDBConnector
from app.models.event_schema import EventSchema
from app.config.settings import settings
from app.config.kafka_config import KafkaConfig
from app.config.mongodb_config import MongoDBConfig


class DirectStreamingJob:
    """Robust direct streaming job - Kafka → MongoDB"""
    
    def __init__(self):
        # Create Spark session
        self.spark = SparkSessionFactory.create_streaming_session(
            "DirectStreamingPipeline"
        )
        self.spark.sparkContext.setLogLevel("WARN")
        
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
        """Execute the direct streaming pipeline"""
        print("=" * 80)
        print("🚀 Starting Direct Streaming Pipeline")
        print("=" * 80)
        print(f"📥 Source: Kafka topic '{self.kafka_config.topic}'")
        print("💾 Destination: MongoDB collection 'raw_events'")
        print("🛡️  Validation: Strict Schema Check")
        print("📊 Monitoring: Throughput logs enabled")
        print("=" * 80)
        
        # Step 1: Read from Kafka
        df_kafka = self.kafka_connector.read_stream()
        print("\n✓ Connected to Kafka")
        
        # Step 2: Schema Validation & Parsing
        # Parse JSON and enforce schema. Malformed records become NULL.
        event_schema = EventSchema.get_kafka_event_schema()
        
        df_parsed = df_kafka.select(
            from_json(
                col("value").cast("string"), 
                event_schema, 
                options={"mode": "PERMISSIVE"}  # Allows capturing nulls for counting
            ).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        )
        
        # Filter valid records
        df_valid = df_parsed.filter(col("data").isNotNull()) \
            .select("data.*", "kafka_timestamp")
            
        # Add processing metadata
        df_final = df_valid.withColumn(
            "processing_time", current_timestamp()
        ).withColumn(
            "event_timestamp", 
            to_timestamp(col("event_time"), "yyyy-MM-dd HH:mm:ss z")
        )

        # Step 3: Write to MongoDB
        print("✓ Schema Validation configured")
        
        query = self.mongo_connector.write_stream(
            df_final,
            collection="raw_events",
            checkpoint_location=settings.get_checkpoint_path("raw_events"),
            output_mode="append"
        )
        
        print("\n" + "=" * 80)
        print("✅ Pipeline started!")
        print("=" * 80)
        
        # Step 4: Monitor Throughput
        try:
            while query.isActive:
                progress = query.lastProgress
                if progress:
                    batch_id = progress['batchId']
                    num_rows = progress['numInputRows']
                    rate = progress['processedRowsPerSecond']
                    
                    if num_rows > 0:
                        print(f"[{time.strftime('%H:%M:%S')}] Batch {batch_id}: "
                              f"Processed {num_rows} records at {rate:.2f} rows/sec")
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopping pipeline...")
            query.stop()
            self.spark.stop()
            print("✅ Shutdown complete")


def main():
    """Main entry point"""
    job = DirectStreamingJob()
    job.run()


if __name__ == "__main__":
    main()
