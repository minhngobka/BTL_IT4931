#for ML
import os, json
from datetime import datetime
from pymongo import MongoClient, ReplaceOne

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark import StorageLevel
from pyspark.ml import PipelineModel

from pyspark.ml.linalg import VectorUDT, DenseVector, SparseVector
from pyspark.sql.types import DoubleType
from pyspark.sql.functions import udf

def get_p_buy(v):
    if isinstance(v, DenseVector) or isinstance(v, SparseVector):
        arr = v.toArray()
        return float(arr[1]) if len(arr) > 1 else float(arr[0])
    return float(v[1]) if isinstance(v, list) and len(v) > 1 else 0.0

udf_p_buy = udf(get_p_buy, DoubleType())

HDFS_NAMENODE = os.getenv("HDFS_NAMENODE", "hdfs://localhost:9000")

CANDIDATES_PATH = os.getenv("CANDIDATES_PATH", "hdfs:///data/outputs/reco_candidates_cooc")
PRODUCT_FEATS_PATH = os.getenv("PRODUCT_FEATS_PATH", "hdfs:///data/outputs/product_features_from_events")

# Model bạn đã train trên HDFS:
MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "hdfs:///user/tuanninh/models/recommendation_model_rf_topk_ohe"
)

OUT_RECS_HDFS = os.getenv("OUT_RECS_HDFS", "hdfs:///data/outputs/recommendations_final")

TOPN_FINAL = int(os.getenv("TOPN_FINAL", "20"))
ALPHA_REL = float(os.getenv("ALPHA_REL", "0.7"))
BETA_ML = float(os.getenv("BETA_ML", "0.3"))

# Bucket giống lúc train
TOP_BRANDS = int(os.getenv("TOP_BRANDS", "200"))
TOP_CATEGORIES = int(os.getenv("TOP_CATEGORIES", "200"))
OTHER_BRAND = "OTHER_BRAND"
OTHER_CAT = "OTHER_CAT"

# Mongo info (dùng chung với recommendation.py)
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGODB_DATABASE", "ecommerce")
MONGO_COLL = os.getenv("RECO_COLLECTION", "recommendations")

def create_spark():
    return (
        SparkSession.builder
        .appName("RerankWithRFModelToMongo")
        .master("local[*]")
        .config("spark.hadoop.fs.defaultFS", HDFS_NAMENODE)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.shuffle.partitions", os.getenv("SPARK_SHUFFLE_PARTITIONS", "64"))
        .getOrCreate()
    )

def keep_topk_and_bucket_other(df, col_name: str, k: int, other_value: str):
    topk_df = (
        df.groupBy(col_name).count()
          .orderBy(F.desc("count"))
          .limit(k)
          .select(col_name)
          .withColumn("_is_top", F.lit(1))
    )
    return (
        df.join(topk_df, on=col_name, how="left")
          .withColumn(col_name, F.when(F.col("_is_top") == 1, F.col(col_name)).otherwise(F.lit(other_value)))
          .drop("_is_top")
    )

def mongo_upsert_partition(rows_iter):
    """
    rows_iter là iterator của JSON string (toJSON).
    Dùng bulk upsert theo product_id.
    """
    client = MongoClient(MONGO_URI)
    coll = client[MONGO_DB][MONGO_COLL]

    ops = []
    now = datetime.utcnow().isoformat()

    for js in rows_iter:
        doc = json.loads(js)
        # đảm bảo updated_at có giá trị string iso
        doc["updated_at"] = doc.get("updated_at") or now
        pid = str(doc["product_id"])

        ops.append(
            ReplaceOne({"product_id": pid}, doc, upsert=True)
        )

        if len(ops) >= 500:
            coll.bulk_write(ops, ordered=False)
            ops = []

    if ops:
        coll.bulk_write(ops, ordered=False)

    client.close()

def main():
    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    candidates = spark.read.parquet(CANDIDATES_PATH)  # product_id, cand_product_id, related_score
    feats = spark.read.parquet(PRODUCT_FEATS_PATH)    # product_id, brand, category_code, price

    # Join candidate features (Y)
    df = (
        candidates.join(
            feats.withColumnRenamed("product_id", "cand_product_id"),
            on="cand_product_id",
            how="left"
        )
        .select("product_id", "cand_product_id", "related_score", "brand", "category_code", "price")
        .dropna(subset=["brand", "category_code", "price"])
    )

    # Persist để tránh recompute
    df = df.persist(StorageLevel.MEMORY_AND_DISK)

    # Bucket brand/category_code cho gần với train
    df = keep_topk_and_bucket_other(df, "brand", TOP_BRANDS, OTHER_BRAND)
    df = keep_topk_and_bucket_other(df, "category_code", TOP_CATEGORIES, OTHER_CAT)

    # Load model + score
    model = PipelineModel.load(MODEL_PATH)
    scored = model.transform(df)

    scored = scored.withColumn("p_buy", udf_p_buy(F.col("probability")))
    scored = scored.withColumn("rel_norm", F.log1p(F.col("related_score")))

    scored = scored.withColumn(
        "final_score",
        F.lit(ALPHA_REL) * F.col("rel_norm") + F.lit(BETA_ML) * F.col("p_buy")
    )

    # TopN per product_id
    w = Window.partitionBy("product_id").orderBy(F.col("final_score").desc())
    topn = (
        scored.withColumn("rn", F.row_number().over(w))
              .filter(F.col("rn") <= TOPN_FINAL)
              .drop("rn")
              .select("product_id", "cand_product_id", "final_score", "related_score", "p_buy")
    )

    # Group -> recs array
    recs = (
        topn.groupBy("product_id")
            .agg(
                F.sort_array(
                    F.collect_list(
                        F.struct(
                            F.col("final_score").alias("score"),
                            F.col("cand_product_id").alias("product_id"),
                            F.col("p_buy").alias("p_buy"),
                            F.col("related_score").alias("related_score")
                        )
                    ),
                    asc=False
                ).alias("recs")
            )
            .withColumn("updated_at", F.date_format(F.current_timestamp(), "yyyy-MM-dd'T'HH:mm:ss"))
    )

    # Save to HDFS (luôn lưu để debug)
    recs.write.mode("overwrite").parquet(OUT_RECS_HDFS)
    print("✅ Saved HDFS recommendations:", OUT_RECS_HDFS)

    # Write to MongoDB (không cần connector)
    # toJSON -> foreachPartition -> bulk upsert
    recs.select("product_id", "recs", "updated_at") \
        .toJSON() \
        .foreachPartition(mongo_upsert_partition)

    print(f"✅ Upserted to MongoDB: {MONGO_DB}.{MONGO_COLL}")

    spark.stop()

if __name__ == "__main__":
    main()
