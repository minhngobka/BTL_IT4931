"""MongoDB-specific configuration"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class MongoDBConfig:
    """MongoDB connection and collection configuration"""
    
    uri: str
    database: str
    
    # Collection names
    ENRICHED_EVENTS: str = "enriched_events"
    EVENT_AGGREGATIONS: str = "event_aggregations"
    USER_SESSION_ANALYTICS: str = "user_session_analytics"
    CONVERSION_FUNNEL: str = "conversion_funnel"
    USER_FEATURES: str = "user_feature_engineering"
    CUSTOMER_SEGMENTS: str = "customer_segments"
    CHURN_PREDICTIONS: str = "churn_predictions"
    TIME_SERIES_ANALYSIS: str = "time_series_analysis"
    PRODUCT_AFFINITY: str = "product_affinity_matrix"
    STATISTICAL_ANALYSIS: str = "statistical_analysis"
    
    def get_spark_write_options(self, collection: str) -> Dict[str, str]:
        """Get MongoDB write options for Spark"""
        return {
            'spark.mongodb.write.connection.uri': self.uri,
            'spark.mongodb.write.database': self.database,
            'spark.mongodb.write.collection': collection,
        }
    
    def get_spark_read_options(self, collection: str) -> Dict[str, str]:
        """Get MongoDB read options for Spark"""
        return {
            'spark.mongodb.read.connection.uri': self.uri,
            'spark.mongodb.read.database': self.database,
            'spark.mongodb.read.collection': collection,
        }
    
    def get_connection_string(self, collection: str = None) -> str:
        """Get full MongoDB connection string"""
        if collection:
            return f"{self.uri}{self.database}.{collection}"
        return f"{self.uri}{self.database}"
