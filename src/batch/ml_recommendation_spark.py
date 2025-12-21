# src/batch/ml_recommendation_spark.py
import os
import sys
from dotenv import load_dotenv

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator

load_dotenv()

HDFS_NAMENODE = os.getenv("HDFS_NAMENODE", "hdfs://localhost:9000")
CSV_PATH = f"{HDFS_NAMENODE}/data/raw/ecommerce_events_2019_oct.csv"

MODEL_PATH_LOCAL = os.getenv("MODEL_PATH_LOCAL", "models/recommendation_model_rf_topk_ohe")

TOP_BRANDS = int(os.getenv("TOP_BRANDS", "200"))
TOP_CATEGORIES = int(os.getenv("TOP_CATEGORIES", "200"))
OTHER_BRAND = "OTHER_BRAND"
OTHER_CAT = "OTHER_CAT"

LIMIT_ROWS = int(os.getenv("LIMIT_ROWS", "50000"))
SEED = 42

def create_spark():
    return (
        SparkSession.builder
        .appName("MLRecommendation-RF-TopK-OHE")
        .master("local[*]")
        .config("spark.hadoop.fs.defaultFS", HDFS_NAMENODE)
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "1g")
        .config("spark.sql.shuffle.partitions", "4")
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
          .withColumn(
              col_name,
              F.when(F.col("_is_top") == 1, F.col(col_name)).otherwise(F.lit(other_value))
          )
          .drop("_is_top")
    )

def train_model():
    spark = create_spark()
    spark.sparkContext.setLogLevel("ERROR")

    try:
        print("📖 Loading data from HDFS (TINY sample)...")
        df = spark.read.csv(CSV_PATH, header=True, inferSchema=False).limit(LIMIT_ROWS)

        print("\n🔧 Preparing features...")
        df = (
            df.select(
                F.col("brand").cast("string").alias("brand"),
                F.col("category_code").cast("string").alias("category_code"),
                F.col("price").cast("double").alias("price"),
                F.when(F.lower(F.col("event_type")) == "purchase", F.lit(1)).otherwise(F.lit(0)).alias("is_purchase")
            )
            .dropna(subset=["brand", "category_code", "price", "is_purchase"])
            .cache()
        )
        print(f"✅ Clean rows: {df.count()}")

        # ===== Phương án B: Top-K + OTHER =====
        print(f"\n📌 Bucketing rare values -> OTHER (Top {TOP_BRANDS} brands, Top {TOP_CATEGORIES} categories)")
        df = keep_topk_and_bucket_other(df, "brand", TOP_BRANDS, OTHER_BRAND)
        df = keep_topk_and_bucket_other(df, "category_code", TOP_CATEGORIES, OTHER_CAT).cache()

        # Optional check
        b_cnt = df.select("brand").distinct().count()
        c_cnt = df.select("category_code").distinct().count()
        print(f"✅ Distinct after bucket: brand={b_cnt}, category_code={c_cnt}")

        # ===== Pipeline: StringIndexer -> OneHot -> Assemble -> RF =====
        print("\n🔗 Building Pipeline...")

        brand_indexer = StringIndexer(
            inputCol="brand",
            outputCol="brand_idx",
            handleInvalid="keep"
        )
        cat_indexer = StringIndexer(
            inputCol="category_code",
            outputCol="cat_idx",
            handleInvalid="keep"
        )

        # OneHot để tránh lỗi maxBins khi category nhiều
        encoder = OneHotEncoder(
            inputCols=["brand_idx", "cat_idx"],
            outputCols=["brand_ohe", "cat_ohe"],
            handleInvalid="keep"
        )

        assembler = VectorAssembler(
            inputCols=["brand_ohe", "cat_ohe", "price"],
            outputCol="features"
        )

        rf = RandomForestClassifier(
            featuresCol="features",
            labelCol="is_purchase",
            numTrees=2,
            maxDepth=3,
            seed=SEED
        )

        pipeline = Pipeline(stages=[brand_indexer, cat_indexer, encoder, assembler, rf])

        train_data, test_data = df.randomSplit([0.8, 0.2], seed=SEED)
        print(f"📊 Train/Test: {train_data.count()} / {test_data.count()}")

        print("\n🤖 Training...")
        pipeline_model = pipeline.fit(train_data)
        print("✅ Model trained!")

        preds = pipeline_model.transform(test_data)
        auc = BinaryClassificationEvaluator(labelCol="is_purchase").evaluate(preds)
        print(f"✅ AUC: {auc:.4f}")

        print("\n💾 Saving PipelineModel...")
        pipeline_model.write().overwrite().save(MODEL_PATH_LOCAL)
        print(f"✅ Saved to {MODEL_PATH_LOCAL}")

        spark.stop()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            spark.stop()
        except:
            pass
        return False

if __name__ == "__main__":
    ok = train_model()
    sys.exit(0 if ok else 1)
