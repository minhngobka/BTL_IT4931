"""Data simulator for Kafka event production"""

import json
import time
import pandas as pd
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from app.config.settings import settings


class EventSimulator:
    """Simulate e-commerce events and send to Kafka"""
    
    def __init__(self, kafka_broker: str = None, topic: str = None):
        self.kafka_broker = kafka_broker or settings.KAFKA_EXTERNAL_BROKER
        self.topic = topic or settings.KAFKA_TOPIC
        self.producer = self._create_producer()
    
    def _create_producer(self) -> KafkaProducer:
        """Create Kafka producer with retry logic"""
        print(f"Connecting to Kafka broker at {self.kafka_broker}...")
        
        while True:
            try:
                producer = KafkaProducer(
                    bootstrap_servers=[self.kafka_broker],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',
                    retries=3
                )
                print("✓ Kafka connection successful!")
                return producer
            except NoBrokersAvailable:
                print("Kafka broker not available. Retrying in 5 seconds...")
                print("Tip: Check 'minikube ip' and verify service is running")
                time.sleep(5)
    
    def send_event(self, event: dict) -> None:
        """Send a single event to Kafka"""
        self.producer.send(self.topic, value=event)
    
    def send_from_csv(self, csv_path: str = None, chunk_size: int = None, 
                     sleep_time: float = None) -> None:
        """
        Read CSV file and send events to Kafka
        
        Args:
            csv_path: Path to CSV file (defaults to settings.CSV_FILE_PATH)
            chunk_size: Number of records per batch (defaults to settings.CHUNK_SIZE)
            sleep_time: Delay between events in seconds (defaults to settings.SLEEP_TIME)
        """
        csv_path = csv_path or settings.CSV_FILE_PATH
        chunk_size = chunk_size or settings.CHUNK_SIZE
        sleep_time = sleep_time or settings.SLEEP_TIME
        
        print(f"Starting CSV reader: {csv_path} (chunk_size={chunk_size})")
        
        try:
            required_columns = [
                'event_time', 'event_type', 'product_id', 'category_id',
                'brand', 'price', 'user_id', 'user_session'
            ]
            
            for chunk_df in pd.read_csv(csv_path, chunksize=chunk_size):
                # Select only required columns
                chunk_df = chunk_df[required_columns]
                
                print(f"\n--- Sending {len(chunk_df)} events ---")
                
                for index, row in chunk_df.iterrows():
                    message = row.to_dict()
                    self.send_event(message)
                    
                    if index % 100 == 0:
                        print(f"Sent: {message['event_type']} - User: {message['user_id']}")
                    
                    time.sleep(sleep_time)
                
                self.producer.flush()
                print("--- Chunk complete ---")
        
        except FileNotFoundError:
            print(f"ERROR: File not found '{csv_path}'")
            print("Tip: Download the dataset from Kaggle and place it in data/raw/")
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            print("\n>>> Event simulation complete <<<")
            self.close()
    
    def close(self) -> None:
        """Close the Kafka producer"""
        if self.producer:
            self.producer.close()


def main():
    """Main entry point for event simulator"""
    simulator = EventSimulator()
    simulator.send_from_csv()


if __name__ == "__main__":
    main()
