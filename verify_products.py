from db.mongo_client import db

count = db.product_catalog.count_documents({})
print(f"✅ {count} products in MongoDB")

sample = db.product_catalog.find_one()
print(f"\nSample:")
print(f"  product_id: {sample.get('product_id')}")
print(f"  product_name: {sample.get('product_name')}")
print(f"  category_name: {sample.get('category_name')}")
print(f"  brand: {sample.get('brand')}")
print(f"  image_url: {sample.get('image_url', 'N/A')[:60]}...")
