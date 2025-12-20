#!/bin/bash
set -e

echo "🔄 Rebuilding Spark Docker image with updated code..."

# Configure Docker to use Minikube
eval $(minikube docker-env)

# Build new image
echo "📦 Building Docker image..."
docker build -t huynambka/bigdata-spark:latest -f deploy/docker/Dockerfile .

echo ""
echo "✅ Image built successfully!"

# Restart deployment to use new image
echo "🔄 Restarting Spark deployment..."
kubectl rollout restart deployment/spark-streaming-with-pvc

echo ""
echo "⏳ Waiting for new pod..."
sleep 10

# Wait for rollout to complete
kubectl rollout status deployment/spark-streaming-with-pvc --timeout=120s

echo ""
NEW_POD=$(kubectl get pods | grep spark-streaming | grep Running | awk '{print $1}')
echo "✅ New pod running: $NEW_POD"

echo ""
echo "📊 Viewing logs (Ctrl+C to exit)..."
sleep 3
kubectl logs -f $NEW_POD
