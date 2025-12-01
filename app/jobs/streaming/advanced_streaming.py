"""
Advanced Streaming Analytics Job
=================================
Real-time processing of e-commerce customer journey events
"""

from app.utils.spark_factory import SparkSessionFactory
from app.connectors.kafka_connector import KafkaConnector
from app.connectors.mongodb_connector import MongoDBConnector
from app.processors.event_enricher import EventEnricher
from app.processors.aggregator import Aggregator
from app.processors.session_analyzer import SessionAnalyzer
from app.config.settings import settings
from app.config.kafka_config import KafkaConfig
from app.config.mongodb_config import MongoDBConfig


class StreamingAdvancedJob:
    """Advanced streaming analytics job for customer journey analysis"""
    
    def __init__(self):
        # Create Spark session
        self.spark = SparkSessionFactory.create_streaming_session(
            "AdvancedCustomerJourneyStreaming"
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
        
        # Initialize processors
        self.enricher = EventEnricher(self.spark)
        
    def run(self):
        """Execute the streaming job"""
        print("=" * 60)
        print("Starting Advanced Streaming Analytics Job")
        print("=" * 60)
        
        # Read from Kafka
        df_kafka = self.kafka_connector.read_stream()
        print("✓ Connected to Kafka")
        
        # Enrich events
        df_enriched = self.enricher.enrich_events(df_kafka)
        print("✓ Event enrichment configured")
        
        # Stream 1: Write enriched events to MongoDB
        query_enriched = self.mongo_connector.write_stream(
            df_enriched,
            collection=self.mongo_config.ENRICHED_EVENTS,
            checkpoint_location=settings.get_checkpoint_path("enriched_events"),
            output_mode="append"
        )
        print(f"✓ Streaming to {self.mongo_config.ENRICHED_EVENTS}")
        
        # Stream 2: Windowed aggregations
        df_windowed = Aggregator.windowed_aggregation(
            df_enriched,
            window_duration="5 minutes",
            watermark_delay="10 minutes"
        )
        
        query_aggregations = self.mongo_connector.write_stream(
            df_windowed,
            collection=self.mongo_config.EVENT_AGGREGATIONS,
            checkpoint_location=settings.get_checkpoint_path("event_aggregations"),
            output_mode="append"
        )
        print(f"✓ Streaming to {self.mongo_config.EVENT_AGGREGATIONS}")
        
        # Stream 3: Session analytics
        df_sessions = SessionAnalyzer.session_metrics(df_enriched)
        
        query_sessions = self.mongo_connector.write_stream(
            df_sessions,
            collection=self.mongo_config.USER_SESSION_ANALYTICS,
            checkpoint_location=settings.get_checkpoint_path("user_sessions"),
            output_mode="update"
        )
        print(f"✓ Streaming to {self.mongo_config.USER_SESSION_ANALYTICS}")
        
        # Stream 4: Conversion funnel
        df_funnel = SessionAnalyzer.conversion_funnel(df_enriched)
        
        query_funnel = self.mongo_connector.write_stream(
            df_funnel,
            collection=self.mongo_config.CONVERSION_FUNNEL,
            checkpoint_location=settings.get_checkpoint_path("conversion_funnel"),
            output_mode="complete"
        )
        print(f"✓ Streaming to {self.mongo_config.CONVERSION_FUNNEL}")
        
        print("\n" + "=" * 60)
        print("All streaming queries started successfully!")
        print("=" * 60)
        print("\nMonitoring streams... (Press Ctrl+C to stop)")
        
        # Wait for all streams
        try:
            query_enriched.awaitTermination()
        except KeyboardInterrupt:
            print("\nStopping streaming queries...")
            self.spark.stop()


def main():
    """Main entry point"""
    job = StreamingAdvancedJob()
    job.run()


if __name__ == "__main__":
    main()
