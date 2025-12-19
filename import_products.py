import pandas as pd
from db.mongo_client import db
import sys

print("📥 Importing products to MongoDB...")

try:
    # Đọc CSV
    df = pd.read_csv('data/catalog/product_catalog.csv')
    print(f"📖 Read {len(df)} products from CSV")
    
    # Xóa collection cũ (nếu có)
    if 'product_catalog' in db.list_collection_names():
        db.product_catalog.drop()
        print("🗑️  Dropped old product_catalog collection")
    
    # Insert products
    products_list = df.to_dict('records')
    result = db.product_catalog.insert_many(products_list)
    print(f"✅ Inserted {len(result.inserted_ids)} products")
    
    # Create index
    db.product_catalog.create_index([("product_id", 1)])
    print("📑 Created index on product_id")
    
    # Verify
    count = db.product_catalog.count_documents({})
    print(f"✅ Verified: {count} products in MongoDB")
    
    # Show sample
    sample = db.product_catalog.find_one()
    print(f"\n📋 Sample product:")
    print(f"   - product_id: {sample.get('product_id')}")
    print(f"   - product_name: {sample.get('product_name')}")
    print(f"   - image_url: {sample.get('image_url', 'N/A')[:50]}...")
    
except Exception as e:
    print(f"❌ Import FAILED: {e}")
    sys.exit(1)

print("\n✅ Import COMPLETED!")
