from kafka import KafkaProducer
import csv, json, time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode()
)

def send_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = 0
        for idx, row in enumerate(reader, start=1):
            # gửi và block tới khi thành công
            producer.send("user_behavior_events", row).get(timeout=10)
            total += 1

            # in tiến trình mỗi 100 dòng
            if idx % 100 == 0:
                print(f"Đã gửi {idx} dòng...")

        # flush đảm bảo tất cả dữ liệu được gửi
        producer.flush()
        print(f"Hoàn tất gửi {total} dòng dữ liệu.")

send_csv("data\\raw\\2019-Oct.csv")