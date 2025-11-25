#!/bin/bash
# Script để demo MongoDB cho giáo viên

echo "╔═══════════════════════════════════════════════╗"
echo "║  🎉 REAL-TIME ANALYTICS - MONGODB DATA        ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Query trực tiếp vào MongoDB pod
kubectl exec deployment/my-mongo-mongodb -- mongosh bigdata_db --quiet --eval '
print("📊 RECORD COUNTS:");
print("  ✓ enriched_events:", db.enriched_events.countDocuments());
print("  ✓ event_aggregations:", db.event_aggregations.countDocuments());
print("  ✓ user_sessions:", db.user_session_analytics.countDocuments());
print("");
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
print("📝 SAMPLE ENRICHED EVENT:");
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
printjson(db.enriched_events.findOne());
print("");
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
print("🔥 TOP 5 MOST VIEWED PRODUCTS:");
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
db.enriched_events.aggregate([
  {$match: {event_type: "view"}},
  {$group: {_id: "$product_id", views: {$sum: 1}}},
  {$sort: {views: -1}},
  {$limit: 5}
]).forEach(function(doc) {
  print("  📦 Product ID " + doc._id + ": " + doc.views + " views");
});
print("");
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
print("👥 TOP 5 MOST ACTIVE USERS:");
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
db.user_session_analytics.aggregate([
  {$group: {_id: "$user_id", total: {$sum: "$total_events"}}},
  {$sort: {total: -1}},
  {$limit: 5}
]).forEach(function(doc) {
  print("  👤 User ID " + doc._id + ": " + doc.total + " events");
});
print("");
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
print("📈 EVENT TYPE DISTRIBUTION:");
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
db.event_aggregations.aggregate([
  {$group: {_id: "$event_type", total: {$sum: "$event_count"}}},
  {$sort: {total: -1}}
]).forEach(function(doc) {
  print("  📊 " + doc._id + ": " + doc.total + " events");
});
print("");
print("✅ Real-time data pipeline is working!");
'

