"""Kafka-specific configuration"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class KafkaConfig:
    """Kafka connection and consumer/producer configuration"""
    
    bootstrap_servers: str
    topic: str
    group_id: str = 'spark-streaming-group'
    auto_offset_reset: str = 'latest'
    enable_auto_commit: bool = False
    
    def get_spark_kafka_options(self) -> Dict[str, str]:
        """Get Kafka options for Spark Structured Streaming"""
        return {
            'kafka.bootstrap.servers': self.bootstrap_servers,
            'subscribe': self.topic,
            'startingOffsets': self.auto_offset_reset,
            'failOnDataLoss': 'false',
            'kafka.session.timeout.ms': '30000',
            'kafka.request.timeout.ms': '40000',
        }
    
    def get_producer_config(self) -> Dict[str, Any]:
        """Get configuration for Kafka producer"""
        return {
            'bootstrap_servers': [self.bootstrap_servers],
            'acks': 'all',
            'retries': 3,
            'max_in_flight_requests_per_connection': 1,
        }
