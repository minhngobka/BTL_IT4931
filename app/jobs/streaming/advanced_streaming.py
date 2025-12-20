"""
Advanced Streaming Job - Complete Processing Pipeline
=====================================================
Full pipeline: Kafka → Parse → Enrich → Aggregate → Analyze → Classify → MongoDB

Features:
- Schema Validation & Parsing
- Data Enrichment (Product + User dimensions)
- Real-time Aggregations (windowed metrics)
- Session Analysis (conversion funnel)
- Behavior Classification (user segments)
- Multiple output collections
- Throughput Monitoring
"""

import time
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, to_timestamp, lit
from app.utils.spark_factory import SparkSessionFactory
from app.connectors.kafka_connector import KafkaConnector
from app.connectors.mongodb_connector import MongoDBConnector
from app.processors.event_enricher import EventEnricher
from app.processors.aggregator import Aggregator
from app.processors.session_analyzer import SessionAnalyzer
from app.processors.behavior_classifier import BehaviorClassifier
from app.models.event_schema import EventSchema
from app.config.settings import settings
from app.config.kafka_config import KafkaConfig
from app.config.mongodb_config import MongoDBConfig


class AdvancedStreamingJob:
    """Complete streaming pipeline with enrichment, aggregation, and classification"""
    
    def __init__(self):
        # Create Spark session
        self.spark = SparkSessionFactory.create_streaming_session(
            "AdvancedStreamingPipeline"
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
        
        # Initialize processors
        self.enricher = EventEnricher(self.spark)
        self.aggregator = Aggregator()
        self.session_analyzer = SessionAnalyzer()
        self.behavior_classifier = BehaviorClassifier()
        
    def run(self):
        """Execute the complete streaming pipeline"""
        print("=" * 80)
        print("🚀 Starting Advanced Streaming Pipeline")
        print("=" * 80)
        print(f"📥 Source: Kafka topic '{self.kafka_config.topic}'")
        print("🔧 Processing Steps:")
        print("   1️⃣  Parse & Validate Schema")
        print("   2️⃣  Enrich (Product + User dimensions)")
        print("   3️⃣  Aggregate (Windowed metrics)")
        print("   4️⃣  Analyze Sessions")
        print("   5️⃣  Classify User Behaviors")
        print("💾 Output: MongoDB (multiple collections)")
        print("=" * 80)
        
        # Step 1: Read from Kafka
        df_kafka = self.kafka_connector.read_stream()
        print("\n✓ Connected to Kafka")
        
        # Step 2: Parse & Validate
        event_schema = EventSchema.get_kafka_event_schema()
        
        df_parsed = df_kafka.select(
            from_json(
                col("value").cast("string"), 
                event_schema, 
                options={"mode": "PERMISSIVE"}
            ).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        )
        
        df_valid = df_parsed.filter(col("data").isNotNull()) \
            .select("data.*", "kafka_timestamp")
        
        print("✓ Schema validation configured")
        
        # Step 3: Enrich with dimension data
        df_enriched = self.enricher.enrich_with_products(df_valid)
        df_enriched = self.enricher.enrich_with_users(df_enriched)
        print("✓ Enrichment configured")
        
        # Add event_timestamp for windowing operations
        df_enriched = df_enriched.withColumn(
            "event_timestamp", 
            to_timestamp(col("event_time"), "yyyy-MM-dd HH:mm:ss z")
        ).withColumn(
            "processing_time", current_timestamp()
        )
        
        # Step 4: Create multiple output streams
        
        # Output 1: Enriched Events (raw enriched data)
        print("✓ Setting up enriched events stream...")
        query_enriched = self.mongo_connector.write_stream(
            df_enriched,
            collection="enriched_events",
            checkpoint_location=settings.get_checkpoint_path("enriched_events"),
            output_mode="append"
        )
        
        # Output 2: Windowed Aggregations
        print("✓ Setting up windowed aggregations...")
        df_windowed = self.aggregator.windowed_aggregation(
            df_enriched,
            window_duration="5 minutes",
            watermark_delay="10 minutes"
        )
        
        query_windowed = self.mongo_connector.write_stream(
            df_windowed,
            collection="windowed_metrics",
            checkpoint_location=settings.get_checkpoint_path("windowed_metrics"),
            output_mode="append"
        )
        
        # Output 3: Session Metrics
        print("✓ Setting up session analysis...")
        df_sessions = self.session_analyzer.session_metrics(df_enriched)
        
        query_sessions = self.mongo_connector.write_stream(
            df_sessions,
            collection="session_metrics",
            checkpoint_location=settings.get_checkpoint_path("session_metrics"),
            output_mode="complete"
        )
        
        # Output 4: User Behavior Classification
        print("✓ Setting up behavior classification...")
        df_session_metrics = self.behavior_classifier.calculate_session_metrics(df_enriched)
        df_behaviors = self.behavior_classifier.classify_behavior(df_session_metrics)
        
        query_behaviors = self.mongo_connector.write_stream(
            df_behaviors,
            collection="user_behaviors",
            checkpoint_location=settings.get_checkpoint_path("user_behaviors"),
            output_mode="complete"
        )
        
        print("\n" + "=" * 80)
        print("✅ All pipelines started!")
        print("=" * 80)
        print("📊 Output Collections:")
        print("   • enriched_events: Raw enriched data")
        print("   • windowed_metrics: 5-min aggregations")
        print("   • session_metrics: Session-level analysis")
        print("   • user_behaviors: User segments (Bouncer/Browser/Engaged/Power)")
        print("=" * 80)
        
        # Monitor all queries
        queries = [query_enriched, query_windowed, query_sessions, query_behaviors]
        query_names = ["Enriched", "Windowed", "Sessions", "Behaviors"]
        
        try:
            while all(q.isActive for q in queries):
                time.sleep(10)
                
                # Print progress for each query
                for name, query in zip(query_names, queries):
                    progress = query.lastProgress
                    if progress and progress.get('numInputRows', 0) > 0:
                        batch_id = progress['batchId']
                        num_rows = progress['numInputRows']
                        rate = progress.get('processedRowsPerSecond', 0)
                        
                        print(f"[{time.strftime('%H:%M:%S')}] {name} Batch {batch_id}: "
                              f"{num_rows} rows @ {rate:.2f} rows/sec")
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopping all pipelines...")
            for query in queries:
                query.stop()
            self.spark.stop()
            print("✅ Shutdown complete")


def main():
    """Main entry point"""
    job = AdvancedStreamingJob()
    job.run()


if __name__ == "__main__":
    main()
