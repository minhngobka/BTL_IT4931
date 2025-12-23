#for ML 
import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark import StorageLevel

HDFS_NAMENODE = os.getenv("HDFS_NAMENODE", "hdfs://localhost:9000")
CSV_PATH = os.getenv("CSV_PATH", f"{HDFS_NAMENODE}/data/raw/ecommerce_events_2019_oct.csv")

# Output HDFS (dùng hdfs:/// để khỏi bị “relative path”)
OUT_CANDIDATES = os.getenv("OUT_CANDIDATES", "hdfs:///data/outputs/reco_candidates_cooc")
OUT_PRODUCT_FEATS = os.getenv("OUT_PRODUCT_FEATS", "hdfs:///data/outputs/product_features_from_events")

# Tuning
TOPK_PER_ITEM = int(os.getenv("TOPK_PER_ITEM", "100"))

# Chống OOM (quan trọng)
MAX_EVENTS_PER_SESSION = int(os.getenv("MAX_EVENTS_PER_SESSION", "25"))  # lấy 25 event gần nhất trong session
MAX_ITEMS_PER_SESSION = int(os.getenv("MAX_ITEMS_PER_SESSION", "60"))    # bỏ session quá dài

# weights
VIEW_W = float(os.getenv("VIEW_W", "1.0"))
PURCHASE_W = float(os.getenv("PURCHASE_W", "5.0"))

# giới hạn chạy thử (0 = không limit)
LIMIT_ROWS = int(os.getenv("LIMIT_ROWS", "0"))

def create_spark():
    return (
        SparkSession.builder
        .appName("BuildCandidatesCooc")
        .master("local[*]")
        .config("spark.hadoop.fs.defaultFS", HDFS_NAMENODE)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.shuffle.partitions", os.getenv("SPARK_SHUFFLE_PARTITIONS", "64"))
        .getOrCreate()
    )

def main():
    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    df = spark.read.csv(CSV_PATH, header=True, inferSchema=False)
    if LIMIT_ROWS and LIMIT_ROWS > 0:
        df = df.limit(LIMIT_ROWS)

    df = (
        df.select(
            F.col("user_session").cast("string").alias("user_session"),
            F.col("event_time").cast("string").alias("event_time"),
            F.lower(F.col("event_type")).alias("event_type"),
            F.col("product_id").cast("string").alias("product_id"),
            F.col("brand").cast("string").alias("brand"),
            F.col("category_code").cast("string").alias("category_code"),
            F.col("price").cast("double").alias("price"),
        )
        .filter(F.col("user_session").isNotNull() & F.col("product_id").isNotNull())
        .filter(F.col("event_type").isin("view", "purchase"))
        .withColumn("event_time_ts", F.to_timestamp("event_time"))
        .filter(F.col("event_time_ts").isNotNull())
    )

    # event weight
    df = df.withColumn(
        "w",
        F.when(F.col("event_type") == "purchase", F.lit(PURCHASE_W)).otherwise(F.lit(VIEW_W))
    )

    # ----------- CHỐNG OOM: giới hạn event per session -----------
    w_sess = Window.partitionBy("user_session").orderBy(F.col("event_time_ts").desc())
    df = (
        df.withColumn("rn", F.row_number().over(w_sess))
          .filter(F.col("rn") <= MAX_EVENTS_PER_SESSION)
          .drop("rn")
    )

    # ----------- product features từ events (cho rerank) -----------
    # Lấy 1 dòng / product_id (đủ brand/category_code/price)
    feats = (
        df.select("product_id", "brand", "category_code", "price")
          .dropna(subset=["brand", "category_code", "price"])
          .dropDuplicates(["product_id"])
    )
    feats.write.mode("overwrite").parquet(OUT_PRODUCT_FEATS)

    # ----------- collapse per (session, product) để giảm trùng -----------
    sess_items = (
        df.groupBy("user_session", "product_id")
          .agg(F.max("w").alias("w_item"))
    )

    # ----------- CHỐNG OOM: bỏ session có quá nhiều items -----------
    sess_size = sess_items.groupBy("user_session").agg(F.count("*").alias("n_items"))
    sess_items = (
        sess_items.join(sess_size, "user_session")
                  .filter(F.col("n_items") <= MAX_ITEMS_PER_SESSION)
                  .drop("n_items")
    )

    # Persist để không tính lại nhiều lần
    sess_items = sess_items.persist(StorageLevel.MEMORY_AND_DISK)

    # ----------- self-join trong session để tạo pair (A,B) -----------
    a = sess_items.alias("a")
    b = sess_items.alias("b")

    pairs = (
        a.join(b, on=F.col("a.user_session") == F.col("b.user_session"))
         .where(F.col("a.product_id") < F.col("b.product_id"))
         .select(
             F.col("a.product_id").alias("itemA"),
             F.col("b.product_id").alias("itemB"),
             (F.col("a.w_item") + F.col("b.w_item")).alias("pair_w")
         )
    )

    # aggregate pair weights across all sessions
    pair_scores = pairs.groupBy("itemA", "itemB").agg(F.sum("pair_w").alias("related_score"))

    # symmetric A->B and B->A
    sym = (
        pair_scores.select(
            F.col("itemA").alias("product_id"),
            F.col("itemB").alias("cand_product_id"),
            F.col("related_score")
        ).unionByName(
            pair_scores.select(
                F.col("itemB").alias("product_id"),
                F.col("itemA").alias("cand_product_id"),
                F.col("related_score")
            )
        )
    )

    # topK per product
    w_top = Window.partitionBy("product_id").orderBy(F.col("related_score").desc())
    topk = (
        sym.withColumn("rn", F.row_number().over(w_top))
           .filter(F.col("rn") <= TOPK_PER_ITEM)
           .drop("rn")
    )

    topk.write.mode("overwrite").parquet(OUT_CANDIDATES)

    print("✅ Saved product feats:", OUT_PRODUCT_FEATS)
    print("✅ Saved candidates:", OUT_CANDIDATES)

    spark.stop()

if __name__ == "__main__":
    main()
