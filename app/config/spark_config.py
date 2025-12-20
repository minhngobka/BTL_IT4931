"""Spark-specific configuration"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class SparkConfig:
    """Spark session configuration"""
    
    app_name: str
    master: str = "local[*]"
    checkpoint_location: str = "/opt/spark/work-dir/checkpoints"
    
    # Performance tuning
    shuffle_partitions: int = 8
    default_parallelism: int = 8
    adaptive_enabled: bool = True
    
    # Streaming specific
    trigger_interval: str = "10 seconds"
    watermark_delay: str = "10 minutes"
    
    def get_spark_conf(self) -> Dict[str, str]:
        """Get Spark configuration as dictionary"""
        return {
            # Shuffle and parallelism
            'spark.sql.shuffle.partitions': str(self.shuffle_partitions),
            'spark.default.parallelism': str(self.default_parallelism),
            
            # Adaptive Query Execution
            'spark.sql.adaptive.enabled': str(self.adaptive_enabled).lower(),
            'spark.sql.adaptive.coalescePartitions.enabled': 'true',
            'spark.sql.adaptive.skewJoin.enabled': 'true',
            
            # Streaming
            'spark.sql.streaming.checkpointLocation': self.checkpoint_location,
            'spark.sql.streaming.stateStore.providerClass': 
                'org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider',
            'spark.sql.streaming.metricsEnabled': 'true',
            
            # Join optimization
            'spark.sql.autoBroadcastJoinThreshold': '10485760',  # 10MB
            
            # Memory management
            'spark.memory.fraction': '0.8',
            'spark.memory.storageFraction': '0.3',
        }
    
    def get_streaming_conf(self) -> Dict[str, str]:
        """Get streaming-specific configuration"""
        return {
            'trigger': self.trigger_interval,
            'watermark': self.watermark_delay,
        }
