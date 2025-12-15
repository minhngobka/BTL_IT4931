"""Central configuration management using environment variables"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / 'config' / '.env'

if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)


class Settings:
    """Central configuration class"""
    
    # Environment
    ENV: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Project paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / 'data'
    LOGS_DIR: Path = BASE_DIR / 'logs'
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        'KAFKA_INTERNAL_BROKER',
        'my-cluster-kafka-bootstrap.default.svc.cluster.local:9092'
    )
    KAFKA_EXTERNAL_BROKER: str = os.getenv('KAFKA_EXTERNAL_BROKER', '192.168.49.2:31927')
    KAFKA_TOPIC: str = os.getenv('KAFKA_TOPIC', 'customer-events')
    
    # MongoDB settings
    MONGODB_URI: str = os.getenv(
        'MONGODB_URI',
        'mongodb://my-mongo-mongodb.default.svc.cluster.local:27017/'
    )
    MONGODB_DATABASE: str = os.getenv('MONGODB_DATABASE', 'bigdata_db')
    
    # Data settings
    CSV_FILE_PATH: str = os.getenv('CSV_FILE_PATH', 'data/raw/ecommerce_events_2019_oct.csv')
    CATALOG_DIR: str = os.getenv('CATALOG_DIR', 'data/catalog')
    
    # Simulator settings
    CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '1000'))
    SLEEP_TIME: float = float(os.getenv('SLEEP_TIME', '0.01'))
    
    # Spark settings
    CHECKPOINT_BASE: str = os.getenv('CHECKPOINT_BASE', '/opt/spark/work-dir/checkpoints')
    SPARK_MASTER: str = os.getenv('SPARK_MASTER', 'local[*]')
    
    @classmethod
    def get_data_path(cls, relative_path: str) -> Path:
        """Get absolute path for data files"""
        return cls.DATA_DIR / relative_path
    
    @classmethod
    def get_catalog_path(cls, filename: str) -> str:
        """Get catalog file path"""
        return str(cls.DATA_DIR / 'catalog' / filename)
    
    @classmethod
    def get_checkpoint_path(cls, job_name: str) -> str:
        """Get checkpoint path for a specific job"""
        return f"{cls.CHECKPOINT_BASE}/{job_name}"


# Create singleton instance
settings = Settings()
