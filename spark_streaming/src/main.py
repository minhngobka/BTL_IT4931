from pyspark.sql import SparkSession
from consumer import read_kafka
from processor import process_data
from writer import write_to_console_with_count

# Tạo Spark Session kết nối với Spark Master trong Docker
spark = SparkSession.builder \
    .appName("KafkaSparkStreaming") \
    .master("spark://spark-master:7077") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .config("spark.executor.memory", "1g") \
    .config("spark.executor.cores", "1") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Kafka config cho Docker network
topic = "user_behavior_events"
bootstrap_servers = "kafka:29092"  # Internal Docker network

print(f"Connecting to Kafka at {bootstrap_servers}")
print(f"Reading from topic: {topic}")

# Đọc dữ liệu Kafka
df = read_kafka(spark, topic, bootstrap_servers)

# Xử lý dữ liệu
df_processed = process_data(df)

# Ghi ra console + in số record đọc được
query_data, query_count = write_to_console_with_count(df_processed)

print("Spark Streaming started. Waiting for data...")

spark.streams.awaitAnyTermination()