# Tên file: journey_analysis.py
import os
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import col, max, when, sum, count, lit, avg, coalesce
from pyspark.sql.types import DoubleType
from datetime import datetime

# --- Cấu hình ---

# 1. Thông tin MongoDB (Đọc từ collection của app streaming)
MONGO_URI_READ = "mongodb://my-mongo-mongodb.default.svc.cluster.local:27017/"
MONGO_DB_NAME_READ = "bigdata_db"
MONGO_COLLECTION_READ = "customer_events" # <-- Collection mà streaming_app.py ghi vào

# 2. Thông tin MongoDB (Ghi ra collection kết quả)
MONGO_URI_WRITE = "mongodb://my-mongo-mongodb.default.svc.cluster.local:27017/"
MONGO_DB_NAME_WRITE = "bigdata_db"
MONGO_COLLECTION_WRITE = "journey_metrics" # <-- Collection mới cho kết quả

def main():
    print("Khởi tạo Spark Session cho Job Phân tích Hành trình (Batch)...")
    
    spark = SparkSession.builder \
        .appName("JourneyAnalysisBatch") \
        .master("local[*]") \
        .config("spark.mongodb.read.connection.uri", f"{MONGO_URI_READ}{MONGO_DB_NAME_READ}.{MONGO_COLLECTION_READ}") \
        .config("spark.mongodb.write.connection.uri", f"{MONGO_URI_WRITE}{MONGO_DB_NAME_WRITE}.{MONGO_COLLECTION_WRITE}") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    print("Spark Session đã sẵn sàng. Đang đọc dữ liệu từ MongoDB...")

    # --- BƯỚC 1: ĐỌC DỮ LIỆU TỪ MONGODB ---
    # Đọc toàn bộ collection 'customer_events'
    df_events = spark.read \
        .format("mongodb") \
        .load()

    # Chuyển đổi kiểu dữ liệu và lọc các event quan trọng
    df_events = df_events \
        .filter(col("event_type").isin("view", "cart", "purchase")) \
        .filter(col("user_session").isNotNull()) \
        .select("user_session", "event_timestamp", "event_type")

    print(f"Đã đọc xong. Bắt đầu phân tích {df_events.count()} sự kiện...")

    # --- BƯỚC 2: ÁP DỤNG WINDOW FUNCTION ĐỂ PHÂN TÍCH PHIÊN ---
    # Đây là yêu cầu "Window functions" của đề bài
    
    # Định nghĩa 1 Window: Phân nhóm theo user_session, sắp xếp theo thời gian
    window_spec = Window.partitionBy("user_session").orderBy("event_timestamp")
    
    # Tạo một Window không bị ràng buộc (để lấy state của cả session)
    window_session_unbounded = window_spec.rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)

    # Sử dụng Window Function (max) để "đánh dấu" cho cả session
    # nếu nó có chứa 'view', 'cart', hoặc 'purchase'
    df_session_state = df_events \
        .withColumn("has_view", max(when(col("event_type") == "view", True)).over(window_session_unbounded)) \
        .withColumn("has_cart", max(when(col("event_type") == "cart", True)).over(window_session_unbounded)) \
        .withColumn("has_purchase", max(when(col("event_type") == "purchase", True)).over(window_session_unbounded))

    # --- BƯỚC 3: LẤY KẾT QUẢ DUY NHẤT CHO MỖI PHIÊN ---
    # Vì tất cả các hàng trong cùng một session giờ đã có state giống nhau,
    # chúng ta chỉ cần lấy 1 hàng duy nhất (distinct) cho mỗi session
    df_session_summary = df_session_state \
        .select("user_session", "has_view", "has_cart", "has_purchase") \
        .distinct() \
        .fillna(False) # Thay thế NULL (nếu có) bằng False

    # Cache lại để tăng tốc tính toán tiếp theo
    df_session_summary.cache()
    print("Đã phân tích xong trạng thái của từng session.")

    # --- BƯỚC 4: TÍNH TOÁN CÁC CHỈ SỐ CHUYỂN ĐỔI (FUNNEL ANALYSIS) ---
    
    # Đếm tổng số session đã được phân tích
    total_sessions = df_session_summary.count()
    if total_sessions == 0:
        print("Lỗi: Không tìm thấy session nào để phân tích.")
        spark.stop()
        return

    # 1. Tổng số session có "view" (Điểm bắt đầu của phễu)
    sessions_with_view = df_session_summary.filter(col("has_view")).count()

    # 2. Số session chuyển đổi từ "view" -> "cart"
    # (Những session có CẢ view VÀ cart)
    sessions_view_and_cart = df_session_summary.filter(
        col("has_view") & col("has_cart")
    ).count()

    # 3. Số session chuyển đổi từ "cart" -> "purchase"
    # (Những session có CẢ view, cart VÀ purchase)
    sessions_view_cart_and_purchase = df_session_summary.filter(
        col("has_view") & col("has_cart") & col("has_purchase")
    ).count()

    print("--- KẾT QUẢ PHÂN TÍCH PHỄU (FUNNEL) ---")
    print(f"Tổng số Session: {total_sessions}")
    print(f"Sessions có 'View': {sessions_with_view}")
    print(f"Sessions có 'View' VÀ 'Cart': {sessions_view_and_cart}")
    print(f"Sessions có 'View', 'Cart' VÀ 'Purchase': {sessions_view_cart_and_purchase}")

    # --- BƯỚC 5: TÍNH TOÁN TỶ LỆ CHUYỂN ĐỔI VÀ DROP-OFF ---
    
    # Tỷ lệ (View -> Cart): % người xem có thêm vào giỏ
    rate_view_to_cart = (sessions_view_and_cart / sessions_with_view) * 100 if sessions_with_view > 0 else 0.0
    
    # Tỷ lệ (Cart -> Purchase): % người thêm vào giỏ có mua hàng
    rate_cart_to_purchase = (sessions_view_cart_and_purchase / sessions_view_and_cart) * 100 if sessions_view_and_cart > 0 else 0.0
    
    # Tỷ lệ rời bỏ (Drop-off) tại bước 'View'
    dropoff_at_view = 100.0 - rate_view_to_cart
    
    # Tỷ lệ rời bỏ (Drop-off) tại bước 'Cart'
    dropoff_at_cart = 100.0 - rate_cart_to_purchase

    print(f"\n--- TỶ LỆ ---")
    print(f"Tỷ lệ chuyển đổi (View -> Cart): {rate_view_to_cart:.2f}%")
    print(f"Tỷ lệ rời bỏ tại 'View' (không cart): {dropoff_at_view:.2f}%")
    print(f"Tỷ lệ chuyển đổi (Cart -> Purchase): {rate_cart_to_purchase:.2f}%")
    print(f"Tỷ lệ rời bỏ tại 'Cart' (không mua): {dropoff_at_cart:.2f}%")

    # --- BƯỚC 6: LƯU KẾT QUẢ VÀO COLLECTION MONGODB MỚI ---
    
    analysis_time = datetime.now()

    results_data = [
        {"metric": "total_sessions", "value": float(total_sessions), "description": "Tổng số phiên (sessions) đã phân tích", "analysis_timestamp": analysis_time},
        {"metric": "sessions_with_view", "value": float(sessions_with_view), "description": "Số phiên có ít nhất 1 sự kiện 'view'", "analysis_timestamp": analysis_time},
        {"metric": "sessions_view_and_cart", "value": float(sessions_view_and_cart), "description": "Số phiên có CẢ 'view' VÀ 'cart'", "analysis_timestamp": analysis_time},
        {"metric": "sessions_view_cart_and_purchase", "value": float(sessions_view_cart_and_purchase), "description": "Số phiên hoàn thành (có 'view', 'cart', và 'purchase')", "analysis_timestamp": analysis_time},
        {"metric": "rate_view_to_cart_percent", "value": round(rate_view_to_cart, 2), "description": "Tỷ lệ % phiên 'view' chuyển đổi thành 'cart'", "analysis_timestamp": analysis_time},
        {"metric": "rate_cart_to_purchase_percent", "value": round(rate_cart_to_purchase, 2), "description": "Tỷ lệ % phiên 'cart' chuyển đổi thành 'purchase'", "analysis_timestamp": analysis_time},
        {"metric": "dropoff_at_view_percent", "value": round(dropoff_at_view, 2), "description": "Tỷ lệ % phiên 'view' nhưng KHÔNG 'cart'", "analysis_timestamp": analysis_time},
        {"metric": "dropoff_at_cart_percent", "value": round(dropoff_at_cart, 2), "description": "Tỷ lệ % phiên 'cart' nhưng KHÔNG 'purchase'", "analysis_timestamp": analysis_time}
    ]
    
    # Tạo DataFrame từ kết quả
    df_results = spark.createDataFrame(results_data)
    
    # Ghi vào MongoDB
    df_results.write \
        .format("mongodb") \
        .mode("append") \
        .option("database", MONGO_DB_NAME_WRITE) \
        .option("collection", MONGO_COLLECTION_WRITE) \
        .save()
        
    print(f"\n>>> Đã lưu kết quả phân tích vào MongoDB: {MONGO_DB_NAME_WRITE}.{MONGO_COLLECTION_WRITE}")
    
    spark.stop()

if __name__ == "__main__":
    main()