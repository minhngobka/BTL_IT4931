"""
Prometheus metrics exporter for Spark Streaming job
Exposes custom metrics for Grafana visualization
"""

from prometheus_client import Counter, Gauge, Histogram, start_http_server
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class BehaviorMetrics:
    """Custom Prometheus metrics for behavior classification"""
    
    def __init__(self):
        # Counters
        self.sessions_total = Counter(
            'spark_streaming_sessions_total',
            'Total number of sessions processed'
        )
        
        self.sessions_by_segment = Counter(
            'spark_streaming_sessions_by_segment',
            'Sessions processed by behavior segment',
            ['segment']
        )
        
        self.records_processed = Counter(
            'spark_streaming_records_processed',
            'Total records processed from Kafka'
        )
        
        # Gauges (current values)
        self.active_sessions = Gauge(
            'spark_streaming_active_sessions',
            'Number of active sessions being processed'
        )
        
        self.segment_distribution = Gauge(
            'spark_streaming_segment_distribution',
            'Current distribution of behavior segments',
            ['segment']
        )
        
        self.processing_latency = Gauge(
            'spark_streaming_processing_latency_ms',
            'Current processing latency in milliseconds'
        )
        
        # Histograms (distributions)
        self.session_duration = Histogram(
            'spark_streaming_session_duration_minutes',
            'Distribution of session durations',
            buckets=[0.5, 1, 2, 5, 10, 15, 30, 60, 120]
        )
        
        self.events_per_session = Histogram(
            'spark_streaming_events_per_session',
            'Distribution of events per session',
            buckets=[1, 3, 5, 10, 20, 30, 50, 100]
        )
        
        logger.info("Prometheus metrics initialized")
    
    def increment_session(self, segment: str):
        """Increment session counter for a specific segment"""
        self.sessions_total.inc()
        self.sessions_by_segment.labels(segment=segment).inc()
    
    def record_session_metrics(self, segment: str, duration: float, events: int):
        """Record metrics for a processed session"""
        self.increment_session(segment)
        self.session_duration.observe(duration)
        self.events_per_session.observe(events)
    
    def update_segment_distribution(self, distribution: Dict[str, int]):
        """Update current segment distribution gauges"""
        for segment, count in distribution.items():
            self.segment_distribution.labels(segment=segment).set(count)
    
    def update_latency(self, latency_ms: float):
        """Update processing latency"""
        self.processing_latency.set(latency_ms)
    
    def start_server(self, port: int = 8080):
        """Start Prometheus metrics HTTP server"""
        try:
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")

# Global metrics instance
metrics = BehaviorMetrics()

def start_metrics_server(port: int = 8080):
    """Start Prometheus metrics server"""
    metrics.start_server(port)
