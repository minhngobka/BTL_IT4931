import json
import time
import os
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from dotenv import load_dotenv
from pyspark.sql import SparkSession

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

# --- Configuration ---
KAFKA_BROKER = os.getenv('KAFKA_EXTERNAL_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'customer_events')
CSV_FILE_PATH = os.getenv('CSV_FILE_PATH', 'hdfs://localhost:9000/data/raw/ecommerce_events_2019_oct.csv')
CSV_LOCAL_PATH = os.getenv('CSV_LOCAL_PATH', 'data/raw/ecommerce_events_2019_oct.csv')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
SLEEP_TIME = float(os.getenv('SLEEP_TIME', '0.01'))

def create_kafka_producer(broker_url):
    """Create Kafka Producer with retry logic"""
    print(f"🔗 Connecting to Kafka Broker at {broker_url}...")
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[broker_url],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("✅ Kafka connection SUCCESS!")
            return producer
        except NoBrokersAvailable:
            print("⏳ Kafka Broker not found. Retrying in 5 seconds...")
            time.sleep(5)

def read_csv_from_hdfs():
    """Read CSV from HDFS using Spark"""
    print("🚀 Initializing Spark Session for HDFS reading...")
    
    spark = SparkSession.builder \
        .appName("EventSimulatorHDFS") \
        .master("local[*]") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://localhost:9000") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"📖 Reading CSV from: {CSV_FILE_PATH}")
    
    try:
        # Read CSV from HDFS
        df = spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(CSV_FILE_PATH)
        
        print(f"✅ Successfully loaded {df.count()} rows from HDFS")
        return df
    except Exception as e:
        print(f"⚠️  HDFS read failed: {e}")
        print(f"⏮️  Falling back to local file: {CSV_LOCAL_PATH}")
        
        try:
            df = spark.read \
                .option("header", "true") \
                .option("inferSchema", "true") \
                .csv(CSV_LOCAL_PATH)
            print(f"✅ Successfully loaded {df.count()} rows from local")
            return df
        except Exception as e2:
            print(f"❌ Both HDFS and local read failed: {e2}")
            return None

def main():
    # Read CSV using Spark
    df_spark = read_csv_from_hdfs()
    if df_spark is None:
        print("❌ Cannot read CSV file. Exiting...")
        return
    
    # Convert to Pandas for easier iteration
    df = df_spark.select([
        'event_time', 'event_type', 'product_id', 'category_id', 
        'brand', 'price', 'user_id', 'user_session'
    ]).toPandas()
    
    print(f"📊 Total events to send: {len(df)}")
    
    # Create Kafka producer
    producer = create_kafka_producer(KAFKA_BROKER)
    
    try:
        # Process in chunks
        for i in range(0, len(df), CHUNK_SIZE):
            chunk = df.iloc[i:i + CHUNK_SIZE]
            
            print(f"\n📤 Sending {len(chunk)} events (batch {i // CHUNK_SIZE + 1})...")
            
            for idx, row in chunk.iterrows():
                message = row.to_dict()
                producer.send(KAFKA_TOPIC, value=message)
                
                if (idx + 1) % 100 == 0:
                    print(f"  ✓ Sent {idx + 1} events")
                
                time.sleep(SLEEP_TIME)
            
            producer.flush()
            print(f"✅ Batch complete")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        print("\n🏁 Event simulation complete!")
        producer.close()

if __name__ == "__main__":
    main()