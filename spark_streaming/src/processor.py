from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

def process_data(df):
    schema = StructType([
        StructField("event_time", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("category_id", StringType(), True),
        StructField("category_code", StringType(), True),
        StructField("brand", StringType(), True),
        StructField("price", StringType(), True),  # để string, hoặc DoubleType nếu muốn convert
        StructField("user_id", StringType(), True),
        StructField("user_session", StringType(), True)
    ])

    # Parse JSON
    df_parsed = df.select(from_json(col("json_str"), schema).alias("data")).select("data.*")

    # Ví dụ filter event_type = "view"
    df_filtered = df_parsed.filter(col("event_type") == "view")

    return df_filtered
