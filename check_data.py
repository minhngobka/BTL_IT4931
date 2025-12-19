from db.mongo_client import db

print("=" * 60)
print("📊 CHECKING MONGODB DATA")
print("=" * 60)

# 1. Check product_catalog
products = db.product_catalog.count_documents({})
print(f"\n1️⃣ product_catalog: {products} documents")
if products > 0:
    sample = db.product_catalog.find_one()
    print(f"   Sample: {sample.get('product_id')} - {sample.get('product_name')}")

# 2. Check customer_events
events = db.customer_events.count_documents({})
print(f"\n2️⃣ customer_events: {events} documents")
if events > 0:
    sample = db.customer_events.find_one()
    print(f"   Sample: {sample}")

# 3. Check user_session_analytics (dùng cho recommendation)
sessions = db.user_session_analytics.count_documents({})
print(f"\n3️⃣ user_session_analytics: {sessions} documents")
if sessions > 0:
    sample = db.user_session_analytics.find_one()
    print(f"   Sample keys: {list(sample.keys())}")
    print(f"   Sample: {sample}")
else:
    print("   ⚠️ NO DATA - This is needed for recommendations!")

# 4. Summary
print("\n" + "=" * 60)
if products > 0 and sessions > 0:
    print("✅ All data present - Recommendation should work!")
elif products > 0 and events > 0 and sessions == 0:
    print("⚠️ Problem: Events exist but user_session_analytics is empty")
    print("   → streaming_advanced.py needs to create user_session_analytics")
elif products == 0:
    print("❌ Problem: No products in database")
    print("   → Run: python import_products.py")
else:
    print("⚠️ Waiting for more data from Event Simulator...")

print("=" * 60)
