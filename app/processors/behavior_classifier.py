"""
User Behavior Classification Processor
======================================
Phân loại user behavior dựa trên session metrics
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, when, lit, count, sum as _sum, avg, min as _min, max as _max,
    countDistinct, unix_timestamp, current_timestamp, to_json, struct,
    array, window, session_window
)
from pyspark.sql.window import Window
from typing import Dict, List


class BehaviorClassifier:
    """Phân loại user behavior thành 4 segments: Bouncer, Browser, Engaged Shopper, Power User"""
    
    # Thresholds cho phân loại
    SEGMENTS = {
        "bouncer": {
            "total_events": (1, 2),
            "duration_min": (0, 1),
            "cart_count": (0, 0),
            "purchase_count": (0, 0),
            "score": 25,
            "color": "🔴"
        },
        "browser": {
            "total_events": (3, 10),
            "duration_min": (1, 10),
            "cart_count": (1, None),
            "purchase_count": (0, 0),
            "score": 50,
            "color": "🟡"
        },
        "engaged_shopper": {
            "total_events": (10, 30),
            "duration_min": (10, 30),
            "cart_count": (2, None),
            "purchase_count": (1, None),
            "score": 75,
            "color": "🟢"
        },
        "power_user": {
            "total_events": (30, None),
            "duration_min": (30, None),
            "purchase_count": (2, None),
            "score": 100,
            "color": "🔵"
        }
    }
    
    @staticmethod
    def calculate_session_metrics(df: DataFrame) -> DataFrame:
        """
        Tính toán session-level metrics từ raw events
        
        Args:
            df: Enriched events DataFrame
            
        Returns:
            Session metrics DataFrame
        """
        
        session_metrics = df.groupBy("user_id", "user_session").agg(
            # Time metrics
            _min("event_timestamp").alias("session_start"),
            _max("event_timestamp").alias("session_end"),
            
            # Event counts
            count("*").alias("total_events"),
            count(when(col("event_type") == "view", 1)).alias("view_count"),
            count(when(col("event_type") == "cart", 1)).alias("cart_count"),
            count(when(col("event_type") == "purchase", 1)).alias("purchase_count"),
            count(when(col("event_type") == "remove_from_cart", 1)).alias("remove_cart_count"),
            
            # Product diversity
            countDistinct("product_id").alias("unique_products"),
            countDistinct("category_code").alias("unique_categories"),
            
            # Revenue (chỉ tính purchase events)
            _sum(when(col("event_type") == "purchase", col("price"))).alias("total_amount"),
            avg(when(col("event_type") == "purchase", col("price"))).alias("avg_purchase_price"),
            
            # Engagement metrics
            avg("price").alias("avg_product_price_viewed"),
            
            current_timestamp().alias("processing_time")
        )
        
        # Calculate session duration in minutes
        session_metrics = session_metrics.withColumn(
            "session_duration_minutes",
            (unix_timestamp("session_end") - unix_timestamp("session_start")) / 60.0
        )
        
        # Handle edge case: single event sessions have 0 duration
        session_metrics = session_metrics.withColumn(
            "session_duration_minutes",
            when(col("session_duration_minutes") == 0, lit(0.1))
            .otherwise(col("session_duration_minutes"))
        )
        
        return session_metrics
    
    @staticmethod
    def classify_behavior(df: DataFrame) -> DataFrame:
        """
        Phân loại user behavior dựa trên session metrics
        
        Priority order: Power User > Engaged Shopper > Browser > Bouncer
        """
        
        classified = df.withColumn(
            "behavior_segment",
            when(
                # 🔵 Power User - Check highest tier first
                (col("total_events") >= 30) &
                (col("session_duration_minutes") >= 30) &
                (col("purchase_count") >= 2),
                lit("power_user")
            )
            .when(
                # 🟢 Engaged Shopper
                (col("total_events").between(10, 29)) &
                (col("session_duration_minutes").between(10, 30)) &
                (col("cart_count") >= 2) &
                (col("purchase_count") >= 1),
                lit("engaged_shopper")
            )
            .when(
                # 🟡 Browser
                (col("total_events").between(3, 10)) &
                (col("session_duration_minutes").between(1, 10)) &
                (col("cart_count") >= 1) &
                (col("purchase_count") == 0),
                lit("browser")
            )
            .when(
                # 🔴 Bouncer
                (col("total_events").between(1, 2)) &
                (col("session_duration_minutes") < 1) &
                (col("cart_count") == 0) &
                (col("purchase_count") == 0),
                lit("bouncer")
            )
            .otherwise(lit("unclassified"))  # Edge cases
        )
        
        # Add segment score (0-100)
        classified = classified.withColumn(
            "segment_score",
            when(col("behavior_segment") == "power_user", lit(100))
            .when(col("behavior_segment") == "engaged_shopper", lit(75))
            .when(col("behavior_segment") == "browser", lit(50))
            .when(col("behavior_segment") == "bouncer", lit(25))
            .otherwise(lit(0))
        )
        
        # Add segment color emoji
        classified = classified.withColumn(
            "segment_color",
            when(col("behavior_segment") == "power_user", lit("🔵"))
            .when(col("behavior_segment") == "engaged_shopper", lit("🟢"))
            .when(col("behavior_segment") == "browser", lit("🟡"))
            .when(col("behavior_segment") == "bouncer", lit("🔴"))
            .otherwise(lit("⚪"))
        )
        
        # Calculate engagement rate (events per minute)
        classified = classified.withColumn(
            "engagement_rate",
            col("total_events") / col("session_duration_minutes")
        )
        
        # Calculate conversion metrics
        classified = classified.withColumn(
            "cart_conversion_rate",
            when(col("view_count") > 0, col("cart_count") / col("view_count") * 100)
            .otherwise(lit(0.0))
        ).withColumn(
            "purchase_conversion_rate",
            when(col("cart_count") > 0, col("purchase_count") / col("cart_count") * 100)
            .otherwise(lit(0.0))
        ).withColumn(
            "overall_conversion_rate",
            when(col("view_count") > 0, col("purchase_count") / col("view_count") * 100)
            .otherwise(lit(0.0))
        )
        
        return classified
    
    @staticmethod
    def generate_recommendations(df: DataFrame) -> DataFrame:
        """
        Tạo personalized recommendations dựa trên segment
        """
        
        recommendations_map = {
            "bouncer": [
                "Improve landing page design",
                "Check traffic source quality",
                "A/B test hero section",
                "Reduce initial load time",
                "Add exit-intent popup with discount"
            ],
            "browser": [
                "Send abandoned cart email within 1 hour",
                "Offer limited-time discount (5-10%)",
                "Show social proof (reviews, ratings)",
                "Add free shipping threshold banner",
                "Display trust badges and secure payment icons"
            ],
            "engaged_shopper": [
                "Recommend complementary products",
                "Offer loyalty points double bonus",
                "Send personalized follow-up email",
                "Cross-sell related categories",
                "Invite to join VIP program"
            ],
            "power_user": [
                "Activate VIP tier benefits immediately",
                "Exclusive early access to sales",
                "Dedicated customer support priority",
                "Personalized product recommendations based on history",
                "Referral program with premium rewards"
            ]
        }
        
        # Create recommendations array based on segment
        df_with_recs = df.withColumn(
            "recommendations",
            when(col("behavior_segment") == "power_user", 
                 array(*[lit(r) for r in recommendations_map["power_user"]]))
            .when(col("behavior_segment") == "engaged_shopper",
                  array(*[lit(r) for r in recommendations_map["engaged_shopper"]]))
            .when(col("behavior_segment") == "browser",
                  array(*[lit(r) for r in recommendations_map["browser"]]))
            .when(col("behavior_segment") == "bouncer",
                  array(*[lit(r) for r in recommendations_map["bouncer"]]))
            .otherwise(array())
        )
        
        # Add action priority (1=highest, 5=lowest)
        df_with_recs = df_with_recs.withColumn(
            "action_priority",
            when(col("behavior_segment") == "power_user", lit(1))  # Retain VIPs
            .when(col("behavior_segment") == "browser", lit(2))     # Convert browsers
            .when(col("behavior_segment") == "engaged_shopper", lit(3))  # Nurture engaged
            .when(col("behavior_segment") == "bouncer", lit(4))     # Optimize landing
            .otherwise(lit(5))
        )
        
        return df_with_recs
    
    @staticmethod
    def calculate_segment_distribution(df: DataFrame) -> DataFrame:
        """
        Tính phân bố segments theo thời gian (5-minute windows)
        """
        
        distribution = df \
            .groupBy(
                window(col("session_start"), "5 minutes"),
                col("behavior_segment")
            ).agg(
                count("*").alias("session_count"),
                avg("segment_score").alias("avg_score"),
                avg("total_events").alias("avg_events"),
                avg("session_duration_minutes").alias("avg_duration"),
                _sum("total_amount").alias("total_revenue"),
                countDistinct("user_id").alias("unique_users")
            )
        
        # Flatten window struct
        distribution = distribution.select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("behavior_segment"),
            col("session_count"),
            col("avg_score"),
            col("avg_events"),
            col("avg_duration"),
            col("total_revenue"),
            col("unique_users"),
            current_timestamp().alias("processing_time")
        )
        
        return distribution
    
    @staticmethod
    def calculate_conversion_funnel(df: DataFrame) -> DataFrame:
        """
        Tính conversion funnel metrics cho mỗi segment
        
        View → Cart → Purchase
        """
        
        funnel = df.groupBy("behavior_segment").agg(
            count("*").alias("total_sessions"),
            countDistinct("user_id").alias("unique_users"),
            _sum("view_count").alias("total_views"),
            _sum("cart_count").alias("total_carts"),
            _sum("purchase_count").alias("total_purchases"),
            avg("session_duration_minutes").alias("avg_session_duration"),
            _sum("total_amount").alias("total_revenue"),
            avg("total_amount").alias("avg_revenue_per_session")
        )
        
        # Calculate conversion rates
        funnel = funnel \
            .withColumn(
                "view_to_cart_rate",
                when(col("total_views") > 0, (col("total_carts") / col("total_views") * 100))
                .otherwise(lit(0.0))
            ).withColumn(
                "cart_to_purchase_rate",
                when(col("total_carts") > 0, (col("total_purchases") / col("total_carts") * 100))
                .otherwise(lit(0.0))
            ).withColumn(
                "overall_conversion_rate",
                when(col("total_views") > 0, (col("total_purchases") / col("total_views") * 100))
                .otherwise(lit(0.0))
            ).withColumn(
                "avg_order_value",
                when(col("total_purchases") > 0, col("total_revenue") / col("total_purchases"))
                .otherwise(lit(0.0))
            ).withColumn(
                "processing_time",
                current_timestamp()
            )
        
        return funnel
