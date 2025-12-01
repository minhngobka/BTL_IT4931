"""Session analysis processor"""

from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import (
    col, count, sum as _sum, avg, min as _min, max as _max,
    countDistinct, unix_timestamp, when, expr
)


class SessionAnalyzer:
    """Analyze user sessions and conversion funnels"""
    
    @staticmethod
    def session_metrics(df: DataFrame) -> DataFrame:
        """
        Calculate session-level metrics
        Tracks: session duration, event counts, conversion funnel
        """
        df_sessions = df.groupBy("user_id", "user_session").agg(
            _min("event_timestamp").alias("session_start"),
            _max("event_timestamp").alias("session_end"),
            count("*").alias("total_events"),
            _sum(when(col("event_type") == "view", 1).otherwise(0)).alias("view_count"),
            _sum(when(col("event_type") == "cart", 1).otherwise(0)).alias("cart_count"),
            _sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("purchase_count"),
            _sum("price").alias("total_revenue"),
            countDistinct("product_id").alias("unique_products"),
            countDistinct("category_name").alias("unique_categories")
        )
        
        # Calculate session duration in minutes
        df_sessions = df_sessions.withColumn(
            "session_duration_minutes",
            (unix_timestamp("session_end") - unix_timestamp("session_start")) / 60
        )
        
        # Add conversion flags
        df_sessions = df_sessions.withColumn(
            "converted_to_cart",
            when(col("cart_count") > 0, True).otherwise(False)
        ).withColumn(
            "converted_to_purchase",
            when(col("purchase_count") > 0, True).otherwise(False)
        )
        
        return df_sessions
    
    @staticmethod
    def conversion_funnel(df: DataFrame) -> DataFrame:
        """
        Calculate conversion funnel metrics
        View → Cart → Purchase
        """
        df_funnel = df.groupBy().agg(
            countDistinct(when(col("event_type") == "view", col("user_session"))).alias("sessions_with_view"),
            countDistinct(when(col("event_type") == "cart", col("user_session"))).alias("sessions_with_cart"),
            countDistinct(when(col("event_type") == "purchase", col("user_session"))).alias("sessions_with_purchase"),
            count("*").alias("total_events")
        )
        
        # Calculate conversion rates
        df_funnel = df_funnel.withColumn(
            "view_to_cart_rate",
            col("sessions_with_cart") / col("sessions_with_view")
        ).withColumn(
            "cart_to_purchase_rate",
            col("sessions_with_purchase") / col("sessions_with_cart")
        ).withColumn(
            "overall_conversion_rate",
            col("sessions_with_purchase") / col("sessions_with_view")
        )
        
        return df_funnel
    
    @staticmethod
    def user_journey_paths(df: DataFrame) -> DataFrame:
        """Analyze common user journey paths"""
        # Order events within sessions
        window_spec = Window.partitionBy("user_session").orderBy("event_timestamp")
        
        df_ordered = df.withColumn("event_sequence", expr("row_number() OVER (PARTITION BY user_session ORDER BY event_timestamp)"))
        
        # Group events by session to create journey paths
        df_journeys = df_ordered.groupBy("user_session").agg(
            expr("collect_list(event_type) as journey_path"),
            count("*").alias("path_length"),
            _max(when(col("event_type") == "purchase", 1).otherwise(0)).alias("ended_in_purchase")
        )
        
        return df_journeys
