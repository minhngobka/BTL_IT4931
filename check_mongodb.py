from pymongo import MongoClient

# Kết nối MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['bigdata_db']

print("\n" + "="*60)
print("📊 MONGODB COLLECTIONS SUMMARY")
print("="*60)

# Collections cần check
collections = ['user_dimension', 'product_catalog', 'category_hierarchy']

for collection_name in collections:
    col = db[collection_name]
    count = col.count_documents({})
    
    print(f"\n📁 {collection_name}:")
    print(f"   📊 Total documents: {count}")
    
    if count > 0:
        # Lấy 1 bản ghi mẫu
        sample = col.find_one()
        print(f"   📋 Sample record:")
        for key, value in list(sample.items())[:5]:  # Show 5 fields
            print(f"      - {key}: {value}")
        print(f"      ... (and more fields)")
    else:
        print(f"   ⚠️  No documents found!")

# Show all collections in database
print(f"\n📂 All collections in 'bigdata_db':")
for col_name in db.list_collection_names():
    count = db[col_name].count_documents({})
    print(f"   - {col_name}: {count} documents")

print("\n✅ Check complete!")