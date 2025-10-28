from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, to_date

spark = SparkSession.builder \
    .appName("RetailRocketBatchLayer") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

df = spark.read.option("header", True).csv("hdfs://namenode:8020/data/events.csv")

df_kpi = df.withColumn("event_date", to_date(col("timestamp")/1000)) \
    .groupBy("event_date", "event").agg(count("*").alias("num_events"))

df_kpi.write.format("delta").mode("overwrite").save("hdfs://namenode:8020/delta/daily_kpis")

print(" Batch ETL completed → saved to Delta Lake (/delta/daily_kpis)")
