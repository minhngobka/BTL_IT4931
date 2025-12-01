from pyspark.sql.functions import count
from pyspark.sql.streaming import DataStreamWriter

def write_to_console_with_count(df):
    # In dữ liệu ra console
    query_data = df.writeStream \
        .outputMode("append") \
        .format("console") \
        .option("truncate", False) \
        .start()

    # Tính tổng số record đọc được
    query_count = df.writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", False) \
        .queryName("count_query") \
        .start()

    return query_data, query_count
