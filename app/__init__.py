"""Big Data Customer Journey Analytics Application"""

__version__ = '1.0.0'
__author__ = 'BTL_IT4931'

from app.config import Settings, KafkaConfig, MongoDBConfig, SparkConfig

__all__ = ['Settings', 'KafkaConfig', 'MongoDBConfig', 'SparkConfig']
