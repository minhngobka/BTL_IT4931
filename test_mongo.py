import sys
sys.path.insert(0, '/home/tuanninh/BigData_Project/BTL_IT4931')

from db.mongo_client import db, client

print("🔌 Testing MongoDB Connection...")

try:
    # Test ping
    client.admin.command('ping')
    print("✅ MongoDB is RUNNING!")
    
    # List databases
    dbs = client.list_database_names()
    print(f"✅ Databases: {dbs}")
    
    # Check our database
    if 'ecommerce' in dbs:
        print(f"✅ 'ecommerce' database exists")
    else:
        print("⚠️ 'ecommerce' database NOT found (will be created later)")
    
    # Check collections
    collections = db.list_collection_names()
    print(f"📦 Collections: {collections if collections else 'None yet'}")
    
except Exception as e:
    print(f"❌ MongoDB Connection FAILED: {e}")
    print("💡 Make sure docker-compose is running!")
    sys.exit(1)

print("\n✅ MongoDB Test PASSED!")
