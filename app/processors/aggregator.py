"""Aggregation processor for analytics"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    window, col, count, sum as _sum, avg, max as _max, min as _min,
    countDistinct, approx_count_distinct
)


class Aggregator:
    """Perform various aggregations on event streams"""
    
    @staticmethod
    def windowed_aggregation(df: DataFrame, window_duration: str = "5 minutes",
                            slide_duration: str = None, watermark_delay: str = "10 minutes") -> DataFrame:
        """
        Perform windowed aggregations
        
        Args:
            df: Input DataFrame with event_timestamp column
            window_duration: Window size (e.g., "5 minutes", "1 hour")
            slide_duration: Slide interval for sliding windows (None for tumbling)
            watermark_delay: Watermark delay for late data handling
        """
        # Apply watermark
        df_watermarked = df.withWatermark("event_timestamp", watermark_delay)
        
        # Create window specification
        if slide_duration:
            window_spec = window(col("event_timestamp"), window_duration, slide_duration)
        else:
            window_spec = window(col("event_timestamp"), window_duration)
        
        # Aggregate (using approx_count_distinct for streaming)
        df_agg = df_watermarked.groupBy(
            window_spec.alias("time_window"),
            col("event_type")
        ).agg(
            count("*").alias("event_count"),
            _sum("price").alias("total_revenue"),
            avg("price").alias("avg_price"),
            approx_count_distinct("user_id").alias("unique_users"),
            approx_count_distinct("product_id").alias("unique_products"),
            approx_count_distinct("user_session").alias("unique_sessions")
        )
        
        return df_agg
    
    @staticmethod
    def category_aggregation(df: DataFrame) -> DataFrame:
        """Aggregate by category"""
        df_agg = df.groupBy("category_name", "event_type").agg(
            count("*").alias("event_count"),
            _sum("price").alias("total_revenue"),
            avg("price").alias("avg_price"),
            approx_count_distinct("user_id").alias("unique_users")
        )
        
        return df_agg
    
    @staticmethod
    def user_aggregation(df: DataFrame) -> DataFrame:
        """Aggregate by user"""
        df_agg = df.groupBy("user_id").agg(
            count("*").alias("total_events"),
            _sum((col("event_type") == "view").cast("int")).alias("view_count"),
            _sum((col("event_type") == "cart").cast("int")).alias("cart_count"),
            _sum((col("event_type") == "purchase").cast("int")).alias("purchase_count"),
            _sum("price").alias("total_spent"),
            avg("price").alias("avg_order_value"),
            approx_count_distinct("product_id").alias("unique_products_viewed")
        )
        
        return df_agg
