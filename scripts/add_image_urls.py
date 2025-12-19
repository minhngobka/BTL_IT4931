import pandas as pd
import os

# Đọc file CSV
csv_path = 'data/catalog/product_catalog.csv'
df = pd.read_csv(csv_path)

# Kiểm tra xem đã có cột image_url chưa
if 'image_url' not in df.columns:
    # Tạo image URLs tự động dựa trên product_id
    # Cách 1: Dùng placeholder.com (đẹp hơn)
    df['image_url'] = df.apply(
        lambda row: f"https://via.placeholder.com/300x300/FF6B6B/FFFFFF?text={row['product_name'].replace(' ', '+')[:20]}",
        axis=1
    )
    
    # Hoặc Cách 2: Dùng loremflickr (randomize)
    # df['image_url'] = df.apply(
    #     lambda row: f"https://loremflickr.com/300/300/electronics?lock={row['product_id']}",
    #     axis=1
    # )
    
    # Hoặc Cách 3: Dùng API ảnh thực (e-commerce)
    # df['image_url'] = df.apply(
    #     lambda row: f"https://api.example.com/product/{row['product_id']}/image.jpg",
    #     axis=1
    # )
    
    # Lưu lại CSV
    df.to_csv(csv_path, index=False)
    print(f"✅ Đã thêm image_url cho {len(df)} sản phẩm!")
    print(f"Sample: {df['image_url'].iloc[0]}")
else:
    print("⚠️ Cột image_url đã tồn tại")