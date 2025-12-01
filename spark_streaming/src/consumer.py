from pyspark.sql import SparkSession

def read_kafka(spark, topic, bootstrap_servers="localhost:9092"):
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", bootstrap_servers) \
        .option("subscribe", topic) \
        .option("startingOffsets", "earliest") \
        .load()

    # Chuyển value từ byte sang string
    df = df.selectExpr("CAST(value AS STRING) as json_str")
    return df
