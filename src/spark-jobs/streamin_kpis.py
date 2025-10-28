from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window
from pyspark.sql.types import StructType, StringType, LongType

schema = StructType() \
    .add("visitorid", StringType()) \
    .add("itemid", StringType()) \
    .add("event", StringType()) \
    .add("timestamp", StringType())

spark = SparkSession.builder \
    .appName("RetailRocketSpeedLayer") \
    .config("spark.cassandra.connection.host", "cassandra-service") \
    .getOrCreate()

df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-service:9092") \
    .option("subscribe", "retail.events") \
    .load()

df = df_raw.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("data")) \
    .select("data.*")

df = df.withColumn("event_time", (col("timestamp") / 1000).cast("timestamp"))

kpi = df.groupBy(
    window(col("event_time"), "1 minute"),
    col("event")
).count().withColumnRenamed("count", "num_events")

query = kpi.writeStream \
    .format("org.apache.spark.sql.cassandra") \
    .option("checkpointLocation", "/tmp/spark-checkpoints/realtime") \
    .option("keyspace", "retailrocket") \
    .option("table", "realtime_kpis") \
    .outputMode("update") \
    .start()

query.awaitTermination()
