import pandas as pd
import json
import time
import os
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in config directory (2 levels up from this file)
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

# --- Cấu hình ---
KAFKA_BROKER = os.getenv('KAFKA_EXTERNAL_BROKER', '192.168.49.2:31927')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'customer_events')
CSV_FILE_PATH = os.getenv('CSV_FILE_PATH', 'data/raw/ecommerce_events_2019_oct.csv')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
SLEEP_TIME = float(os.getenv('SLEEP_TIME', '0.01'))

def create_kafka_producer(broker_url):
    """Tạo Kafka Producer, thử kết nối lại nếu thất bại."""
    print(f"Đang kết nối tới Kafka Broker tại {broker_url}...")
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[broker_url],
                # Encode message thành JSON bytes
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print(">>> Kết nối Kafka THÀNH CÔNG!")
            return producer
        except NoBrokersAvailable:
            print("Chưa tìm thấy Kafka Broker. Đang thử lại sau 5 giây...")
            print("MẸO: Bạn đã chạy 'minikube ip' và 'kubectl get service ...' đúng chưa?")
            time.sleep(5)

def main():
    producer = create_kafka_producer(KAFKA_BROKER)
    
    print(f"Bắt đầu đọc file: {CSV_FILE_PATH} (chunksize={CHUNK_SIZE})")

    try:
        # Đọc file CSV theo từng "chunk" (lô) để không load hết vào RAM
        for chunk_df in pd.read_csv(CSV_FILE_PATH, chunksize=CHUNK_SIZE):
            
            # Chỉ lấy các cột cần thiết cho chủ đề Customer Journey
            chunk_df = chunk_df[['event_time', 'event_type', 'product_id', 'category_id', 'brand', 'price', 'user_id', 'user_session']]
            
            print(f"\n--- Gửi {len(chunk_df)} sự kiện ---")
            
            # Lặp qua từng dòng trong chunk và gửi tới Kafka
            for index, row in chunk_df.iterrows():
                # Chuyển row thành dictionary (JSON)
                message = row.to_dict()
                
                # Gửi message
                producer.send(KAFKA_TOPIC, value=message)
                
                print(f"Sent: {message['event_type']} - User: {message['user_id']}")
                
                # Nghỉ một chút để giả lập real-time
                time.sleep(SLEEP_TIME)

            producer.flush() # Đẩy hết message đi
            print(f"--- Đã gửi xong chunk ---")

    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file '{CSV_FILE_PATH}'.")
        print("MẸO: Bạn đã tải file .csv từ Kaggle và đặt vào cùng thư mục chưa?")
    except Exception as e:
        print(f"Một lỗi đã xảy ra: {e}")
    finally:
        print("\n>>> ĐÃ GỬI TẤT CẢ DỮ LIỆU TỪ FILE CSV! (hoặc script đã dừng) <<<")
        producer.close()

if __name__ == "__main__":
    main()