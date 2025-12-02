"""
User Behavior Classification Streaming Job
==========================================
Real-time classification của user behavior thành 4 segments:
- 🔴 Bouncer: 1-2 events, <1 min
- 🟡 Browser: 3-10 events, browsing but not buying
- 🟢 Engaged Shopper: 10-30 events, active purchases
- 🔵 Power User: 30+ events, VIP customers
"""

from app.utils.spark_factory import SparkSessionFactory
from app.connectors.kafka_connector import KafkaConnector
from app.connectors.mongodb_connector import MongoDBConnector
from app.processors.event_enricher import EventEnricher
from app.processors.behavior_classifier import BehaviorClassifier
from app.config.settings import settings
from app.config.kafka_config import KafkaConfig
from app.config.mongodb_config import MongoDBConfig


class UserBehaviorStreamingJob:
    """User Behavior Classification Streaming Job"""
    
    def __init__(self):
        # Create Spark session
        self.spark = SparkSessionFactory.create_streaming_session(
            "UserBehaviorClassification"
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
        """Execute the user behavior classification pipeline"""
        print("=" * 80)
        print("🚀 Starting User Behavior Classification Streaming Job")
        print("=" * 80)
        print("\n📊 Classification Segments:")
        print("  🔴 Bouncer (1-2 events, <1 min)")
        print("  🟡 Browser (3-10 events, cart but no purchase)")
        print("  🟢 Engaged Shopper (10-30 events, active purchases)")
        print("  🔵 Power User (30+ events, VIP customers)")
        print("\n" + "=" * 80)
        
        # Step 1: Read from Kafka
        df_kafka = self.kafka_connector.read_stream()
        print("✓ Connected to Kafka topic:", self.kafka_config.topic)
        
        # Step 2: Enrich events with product/user data
        df_enriched = self.enricher.enrich_events(df_kafka)
        print("✓ Event enrichment configured")
        
        # Step 3: Calculate session metrics
        df_session_metrics = BehaviorClassifier.calculate_session_metrics(df_enriched)
        print("✓ Session metrics calculation configured")
        
        # Step 4: Classify user behavior
        df_classified = BehaviorClassifier.classify_behavior(df_session_metrics)
        print("✓ Behavior classification logic applied")
        
        # Step 5: Generate recommendations
        df_with_recommendations = BehaviorClassifier.generate_recommendations(df_classified)
        print("✓ Personalized recommendations generated")
        
        # ===================================================================
        # STREAM 1: User Behavior Segments (Main Output)
        # ===================================================================
        query_behavior_segments = self.mongo_connector.write_stream(
            df_with_recommendations.select(
                "user_id",
                "user_session",
                "behavior_segment",
                "segment_color",
                "segment_score",
                "session_start",
                "session_end",
                "session_duration_minutes",
                "total_events",
                "view_count",
                "cart_count",
                "purchase_count",
                "unique_products",
                "unique_categories",
                "total_amount",
                "engagement_rate",
                "cart_conversion_rate",
                "purchase_conversion_rate",
                "overall_conversion_rate",
                "recommendations",
                "action_priority",
                "processing_time"
            ),
            collection=self.mongo_config.USER_BEHAVIOR_SEGMENTS,
            checkpoint_location=settings.get_checkpoint_path("user_behavior_segments"),
            output_mode="append"
        )
        print(f"✓ Stream 1: {self.mongo_config.USER_BEHAVIOR_SEGMENTS} (append mode)")
        
        # ===================================================================
        # STREAM 2: Segment Distribution (5-minute windows)
        # ===================================================================
        df_distribution = BehaviorClassifier.calculate_segment_distribution(df_classified)
        
        query_distribution = self.mongo_connector.write_stream(
            df_distribution,
            collection=self.mongo_config.SEGMENT_DISTRIBUTION,
            checkpoint_location=settings.get_checkpoint_path("segment_distribution"),
            output_mode="append"
        )
        print(f"✓ Stream 2: {self.mongo_config.SEGMENT_DISTRIBUTION} (append mode)")
        
        # ===================================================================
        # STREAM 3: Conversion Funnel by Segment (Complete mode)
        # ===================================================================
        df_funnel = BehaviorClassifier.calculate_conversion_funnel(df_classified)
        
        query_funnel = self.mongo_connector.write_stream(
            df_funnel,
            collection=self.mongo_config.CONVERSION_FUNNEL,
            checkpoint_location=settings.get_checkpoint_path("conversion_funnel"),
            output_mode="complete"
        )
        print(f"✓ Stream 3: {self.mongo_config.CONVERSION_FUNNEL} (complete mode)")
        
        # ===================================================================
        # STREAM 4: Enriched Events (Raw events for analysis)
        # ===================================================================
        query_enriched = self.mongo_connector.write_stream(
            df_enriched,
            collection=self.mongo_config.ENRICHED_EVENTS,
            checkpoint_location=settings.get_checkpoint_path("enriched_events"),
            output_mode="append"
        )
        print(f"✓ Stream 4: {self.mongo_config.ENRICHED_EVENTS} (append mode)")
        
        print("\n" + "=" * 80)
        print("✅ All streaming queries started successfully!")
        print("=" * 80)
        print("\n📈 Monitoring streams... (Press Ctrl+C to stop)")
        print("\nStreaming to MongoDB collections:")
        print(f"  1. {self.mongo_config.USER_BEHAVIOR_SEGMENTS}")
        print(f"  2. {self.mongo_config.SEGMENT_DISTRIBUTION}")
        print(f"  3. {self.mongo_config.CONVERSION_FUNNEL}")
        print(f"  4. {self.mongo_config.ENRICHED_EVENTS}")
        print("\n" + "=" * 80)
        
        # Wait for all streams
        try:
            query_behavior_segments.awaitTermination()
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping streaming queries...")
            self.spark.stop()
            print("✅ Graceful shutdown complete")


def main():
    """Main entry point"""
    job = UserBehaviorStreamingJob()
    job.run()


if __name__ == "__main__":
    main()
