"""Event data schema definitions"""

from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, 
    DoubleType, TimestampType
)


class EventSchema:
    """Schema definitions for e-commerce events"""
    
    @staticmethod
    def get_kafka_event_schema() -> StructType:
        """Schema for events from Kafka"""
        return StructType([
            StructField("event_time", StringType(), nullable=False),
            StructField("event_type", StringType(), nullable=False),
            StructField("product_id", LongType(), nullable=False),
            StructField("category_id", LongType(), nullable=True),
            StructField("category_code", StringType(), nullable=True),
            StructField("brand", StringType(), nullable=True),
            StructField("price", DoubleType(), nullable=True),
            StructField("user_id", LongType(), nullable=False),
            StructField("user_session", StringType(), nullable=False),
        ])
    
    @staticmethod
    def get_enriched_schema() -> StructType:
        """Schema for enriched events with product metadata"""
        return StructType([
            StructField("event_timestamp", TimestampType(), nullable=False),
            StructField("event_type", StringType(), nullable=False),
            StructField("product_id", LongType(), nullable=False),
            StructField("product_name", StringType(), nullable=True),
            StructField("category_name", StringType(), nullable=True),
            StructField("subcategory", StringType(), nullable=True),
            StructField("brand", StringType(), nullable=True),
            StructField("price", DoubleType(), nullable=True),
            StructField("user_id", LongType(), nullable=False),
            StructField("user_session", StringType(), nullable=False),
            StructField("user_segment", StringType(), nullable=True),
        ])
