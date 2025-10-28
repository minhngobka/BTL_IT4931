from kafka import KafkaProducer
import json, time, csv

producer = KafkaProducer(
    bootstrap_servers='kafka-service:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

with open('/data/events.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        msg = {
            "visitorid": row["visitorid"],
            "itemid": row["itemid"],
            "event": row["event"],
            "timestamp": row["timestamp"]
        }
        producer.send('retail.events', msg)
        time.sleep(0.2)  

print(" Data stream started → Kafka topic: retail.events")
