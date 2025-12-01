"""Event enrichment processor"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, coalesce
from app.models.event_schema import EventSchema
from app.models.product_schema import ProductSchema
from app.models.user_schema import UserSchema
from app.config.settings import settings


class EventEnricher:
    """Enrich raw events with dimension data"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self._load_dimensions()
    
    def _load_dimensions(self):
        """Load dimension tables for enrichment"""
        # Load product catalog
        self.df_products = self.spark.read \
            .schema(ProductSchema.get_catalog_schema()) \
            .option("header", "true") \
            .csv(settings.get_catalog_path("product_catalog.csv")) \
            .hint("broadcast")
        
        # Load user dimension if exists
        try:
            self.df_users = self.spark.read \
                .schema(UserSchema.get_user_dimension_schema()) \
                .option("header", "true") \
                .csv(settings.get_catalog_path("user_dimension.csv")) \
                .hint("broadcast")
        except Exception:
            self.df_users = None
    
    def parse_kafka_events(self, df_kafka: DataFrame) -> DataFrame:
        """Parse Kafka value column to structured events"""
        event_schema = EventSchema.get_kafka_event_schema()
        
        df_parsed = df_kafka.select(
            from_json(col("value").cast("string"), event_schema).alias("event")
        ).select("event.*")
        
        # Convert event_time to timestamp
        df_parsed = df_parsed.withColumn(
            "event_timestamp",
            to_timestamp(col("event_time"), "yyyy-MM-dd HH:mm:ss z")
        )
        
        return df_parsed
    
    def enrich_with_products(self, df_events: DataFrame) -> DataFrame:
        """Join events with product catalog"""
        df_enriched = df_events.join(
            self.df_products,
            on="product_id",
            how="left"
        )
        
        return df_enriched
    
    def enrich_with_users(self, df_events: DataFrame) -> DataFrame:
        """Join events with user dimension"""
        if self.df_users is None:
            return df_events
        
        df_enriched = df_events.join(
            self.df_users,
            on="user_id",
            how="left"
        )
        
        return df_enriched
    
    def enrich_events(self, df_kafka: DataFrame) -> DataFrame:
        """Full enrichment pipeline"""
        df_parsed = self.parse_kafka_events(df_kafka)
        df_enriched = self.enrich_with_products(df_parsed)
        df_enriched = self.enrich_with_users(df_enriched)
        
        return df_enriched
