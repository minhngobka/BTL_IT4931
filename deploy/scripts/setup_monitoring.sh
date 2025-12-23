#!/bin/bash

set -e

echo "Setting up Monitoring Stack (Prometheus + Grafana + Spark UI)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Deploy Prometheus
echo -e "${YELLOW}Deploying Prometheus...${NC}"
kubectl apply -f /workspaces/BTL_IT4931/deploy/kubernetes/monitoring/prometheus-config.yaml

sleep 5

# Deploy Grafana
echo -e "${YELLOW}Deploying Grafana...${NC}"
kubectl apply -f /workspaces/BTL_IT4931/deploy/kubernetes/monitoring/grafana.yaml

sleep 5

# Deploy Dashboard
echo -e "${YELLOW}Deploying Behavior Classification Dashboard...${NC}"
kubectl apply -f /workspaces/BTL_IT4931/deploy/kubernetes/monitoring/behavior-dashboard.yaml

# Expose Spark UI
echo -e "${YELLOW}Exposing Spark UI...${NC}"
kubectl apply -f /workspaces/BTL_IT4931/deploy/kubernetes/monitoring/spark-ui-service.yaml

# Wait for pods to be ready
echo -e "${YELLOW}Waiting for monitoring stack to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=prometheus --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=grafana --timeout=120s || true

echo -e "${GREEN}Monitoring stack deployed!${NC}"

# Port forward services
echo ""
echo "Starting port-forwards for local access..."
echo ""

# Kill existing port-forwards
pkill -f "port-forward.*grafana" 2>/dev/null || true
pkill -f "port-forward.*prometheus" 2>/dev/null || true
pkill -f "port-forward.*spark-ui" 2>/dev/null || true

sleep 2

# Grafana
kubectl port-forward svc/grafana 3000:3000 > /dev/null 2>&1 &
GRAFANA_PID=$!

# Prometheus
kubectl port-forward svc/prometheus 9090:9090 > /dev/null 2>&1 &
PROMETHEUS_PID=$!

# Spark UI
kubectl port-forward svc/spark-streaming-svc 4040:4040 > /dev/null 2>&1 &
SPARK_UI_PID=$!

sleep 5

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Monitoring Stack is Ready!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Grafana Dashboard:"
echo "     URL: http://localhost:3000"
echo "     Username: admin"
echo "     Password: admin123"
echo ""
echo "  Prometheus:"
echo "     URL: http://localhost:9090"
echo ""
echo "  Spark UI:"
echo "     URL: http://localhost:4040"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Tips:"
echo "   - Grafana dashboards auto-refresh every 5 seconds"
echo "   - Check Spark UI 'Streaming' tab for real-time metrics"
echo "   - Use Prometheus for raw metrics queries"
echo ""
echo "To stop port-forwards:"
echo "   kill $GRAFANA_PID $PROMETHEUS_PID $SPARK_UI_PID"
echo ""
echo "View Grafana logs:"
echo "   kubectl logs -f deployment/grafana"
echo ""

# Open browsers (if $BROWSER is set)
if [ -n "$BROWSER" ]; then
    echo "Opening monitoring dashboards in browser..."
    sleep 3
    "$BROWSER" http://localhost:3000 &
    "$BROWSER" http://localhost:4040 &
fi

echo "Setup complete! Press Ctrl+C to stop port-forwards"
echo ""

# Keep script running
wait
