#!/bin/bash
set -e

echo "🗑️  Cleaning up checkpoints and MongoDB data..."

# Get pod names
SPARK_POD=$(kubectl get pods | grep spark-streaming | awk '{print $1}')
MONGO_POD=$(kubectl get pods | grep mongo | grep -v exporter | awk '{print $1}')

if [ -z "$SPARK_POD" ]; then
    echo "Warning: No Spark pod found, skipping checkpoint cleanup"
else
    echo "Spark pod: $SPARK_POD"
    echo "Removing old checkpoints..."
    kubectl exec $SPARK_POD -- rm -rf /tmp/spark-checkpoints/raw_events || true
    kubectl exec $SPARK_POD -- rm -rf /tmp/spark-checkpoints/enriched_events || true
    kubectl exec $SPARK_POD -- rm -rf /tmp/spark-checkpoints/windowed_metrics || true
    kubectl exec $SPARK_POD -- rm -rf /tmp/spark-checkpoints/session_metrics || true
    kubectl exec $SPARK_POD -- rm -rf /tmp/spark-checkpoints/user_behaviors || true
    echo "Checkpoints cleaned"
fi

if [ -z "$MONGO_POD" ]; then
    echo "Warning: No MongoDB pod found, skipping database cleanup"
else
    echo "MongoDB pod: $MONGO_POD"
    echo "Dropping bigdata_db database..."
    kubectl exec $MONGO_POD -- mongosh bigdata_db --eval "db.dropDatabase()"
    echo "Database cleaned"
fi

echo ""
echo "Cleanup complete!"
echo ""
echo "Next steps:"
echo "   1. Run: bash update_spark_code.sh"
echo "   2. Start event simulator to send new data"
