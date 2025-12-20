#!/bin/bash

# Quick script to view metrics without Grafana

echo "📊 User Behavior Classification Metrics"
echo "========================================"
echo ""

# Check if MongoDB pod is running
if ! kubectl get pod -l app.kubernetes.io/name=mongodb &>/dev/null; then
    echo "❌ MongoDB pod not found"
    exit 1
fi

# Get MongoDB pod name
MONGO_POD=$(kubectl get pod -l app.kubernetes.io/name=mongodb -o jsonpath='{.items[0].metadata.name}')

echo "Querying MongoDB metrics..."
echo ""

# Execute queries
kubectl exec -it "$MONGO_POD" -- mongosh bigdata --quiet --eval '
// Segment Distribution
print("🎯 Segment Distribution:");
print("========================");
db.user_behavior_segments.aggregate([
  {$group: {
    _id: "$behavior_segment",
    count: {$sum: 1},
    avg_score: {$avg: "$segment_score"}
  }},
  {$sort: {count: -1}}
]).forEach(doc => {
  const bar = "█".repeat(Math.floor(doc.count / 10));
  print(`${doc._id.padEnd(20)} ${doc.count.toString().padStart(5)} sessions ${bar}`);
  print(`                     Avg Score: ${doc.avg_score.toFixed(2)}`);
  print("");
});

print("\n💰 Revenue by Segment:");
print("======================");
db.user_behavior_segments.aggregate([
  {$addFields: {
    revenue: {
      $toDouble: {
        $ifNull: [
          {$getField: {field: "total_amount", input: {$objectToArray: "$session_metrics"}}},
          "0"
        ]
      }
    }
  }},
  {$group: {
    _id: "$behavior_segment",
    total_revenue: {$sum: "$revenue"},
    avg_revenue: {$avg: "$revenue"},
    sessions: {$sum: 1}
  }},
  {$sort: {total_revenue: -1}}
]).forEach(doc => {
  print(`${doc._id.padEnd(20)} $${doc.total_revenue.toFixed(2)}`);
  print(`                     Avg: $${doc.avg_revenue.toFixed(2)} per session`);
  print("");
});

print("\n📈 Conversion Funnel:");
print("====================");
db.conversion_funnel.find().forEach(doc => {
  print(`${doc.behavior_segment.padEnd(20)}`);
  print(`  View → Cart:     ${doc.view_to_cart_rate.toFixed(2)}%`);
  print(`  Cart → Purchase: ${doc.cart_to_purchase_rate.toFixed(2)}%`);
  print(`  Overall:         ${doc.overall_conversion_rate.toFixed(2)}%`);
  print("");
});

print("\n⏱️  Recent Sessions (Last 10):");
print("==============================");
db.user_behavior_segments.find()
  .sort({timestamp: -1})
  .limit(10)
  .forEach(doc => {
    print(`User ${doc.user_id} - ${doc.behavior_segment} (Score: ${doc.segment_score})`);
    print(`  Session: ${doc.session_id}`);
    print(`  Time: ${doc.timestamp}`);
    print("");
  });

print("\n📊 Summary Statistics:");
print("======================");
const stats = db.user_behavior_segments.aggregate([
  {$facet: {
    total: [{$count: "count"}],
    avgScore: [{$group: {_id: null, avg: {$avg: "$segment_score"}}}],
    segments: [{$group: {_id: "$behavior_segment", count: {$sum: 1}}}]
  }}
]).toArray()[0];

print(`Total Sessions Classified: ${stats.total[0].count}`);
print(`Average Segment Score: ${stats.avgScore[0].avg.toFixed(2)}`);
print("");

print("✅ Metrics retrieved successfully!");
'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 For real-time visualization, use:"
echo "   bash deploy/scripts/setup_monitoring.sh"
echo ""
echo "   Then visit http://localhost:3000 (Grafana)"
echo ""
