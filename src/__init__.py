# check_kafka.py
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'customer_events',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    consumer_timeout_ms=5000
)

print("✓ Listening to Kafka topic 'customer_events'...")

for msg in consumer:
    print(msg.value.decode('utf-8'))
