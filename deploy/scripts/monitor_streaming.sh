#!/bin/bash

# Real-time monitoring script for Spark Streaming

echo "User Behavior Classification - Live Monitor"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Spark pod is running
SPARK_POD=$(kubectl get pod -l app=spark-streaming-pvc -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$SPARK_POD" ]; then
    echo -e "${RED}Spark streaming pod not found${NC}"
    echo "Run: kubectl apply -f deploy/kubernetes/base/spark-deployments.yaml"
    exit 1
fi

# Check pod status
POD_STATUS=$(kubectl get pod "$SPARK_POD" -o jsonpath='{.status.phase}')
if [ "$POD_STATUS" != "Running" ]; then
    echo -e "${YELLOW}Spark pod status: $POD_STATUS${NC}"
    echo "Waiting for pod to be ready..."
    kubectl wait --for=condition=ready pod "$SPARK_POD" --timeout=120s
fi

echo -e "${GREEN}Spark streaming pod: $SPARK_POD${NC}"
echo ""

# Display menu
while true; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Select monitoring option:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  1) View Spark Application Logs"
    echo "  2) View Streaming Query Status"
    echo "  3) View MongoDB Collections"
    echo "  4) View Segment Distribution (Live)"
    echo "  5) Open Spark UI (port-forward)"
    echo "  6) Open Grafana Dashboard"
    echo "  7) View Prometheus Metrics"
    echo "  8) Monitor All (tail logs)"
    echo "  9) Exit"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -n "  Enter choice [1-9]: "
    read choice
    
    case $choice in
        1)
            echo ""
            echo -e "${BLUE}Spark Application Logs:${NC}"
            kubectl logs "$SPARK_POD" --tail=50
            echo ""
            read -p "Press Enter to continue..."
            ;;
        2)
            echo ""
            echo -e "${BLUE}Streaming Query Status:${NC}"
            kubectl exec -it "$SPARK_POD" -- bash -c "
                echo 'Checking Spark streaming queries...'
                ps aux | grep spark-submit
                echo ''
                echo 'Active streaming queries:'
                ls -la /opt/spark/work-dir/checkpoints/ 2>/dev/null || echo 'No checkpoints found'
            "
            echo ""
            read -p "Press Enter to continue..."
            ;;
        3)
            echo ""
            echo -e "${BLUE}MongoDB Collections:${NC}"
            MONGO_POD=$(kubectl get pod -l app.kubernetes.io/name=mongodb -o jsonpath='{.items[0].metadata.name}')
            kubectl exec -it "$MONGO_POD" -- mongosh bigdata --quiet --eval '
                print("Collections in bigdata:");
                db.getCollectionNames().forEach(c => {
                    const count = db[c].countDocuments();
                    print(`  ${c}: ${count} documents`);
                });
            '
            echo ""
            read -p "Press Enter to continue..."
            ;;
        4)
            echo ""
            echo -e "${BLUE}Live Segment Distribution:${NC}"
            bash /workspaces/BTL_IT4931/deploy/scripts/view_metrics.sh
            echo ""
            read -p "Press Enter to continue..."
            ;;
        5)
            echo ""
            echo -e "${YELLOW}Starting Spark UI port-forward...${NC}"
            pkill -f "port-forward.*spark.*4040" 2>/dev/null || true
            kubectl port-forward "$SPARK_POD" 4040:4040 > /dev/null 2>&1 &
            PF_PID=$!
            sleep 2
            echo -e "${GREEN}Spark UI available at: http://localhost:4040${NC}"
            if [ -n "$BROWSER" ]; then
                "$BROWSER" http://localhost:4040 &
            fi
            echo ""
            echo "Press Enter to stop port-forward and continue..."
            read
            kill $PF_PID 2>/dev/null || true
            ;;
        6)
            echo ""
            echo -e "${YELLOW}Starting Grafana port-forward...${NC}"
            pkill -f "port-forward.*grafana" 2>/dev/null || true
            kubectl port-forward svc/grafana 3000:3000 > /dev/null 2>&1 &
            GRAFANA_PID=$!
            sleep 2
            echo -e "${GREEN}Grafana available at: http://localhost:3000${NC}"
            echo "   Username: admin"
            echo "   Password: admin123"
            if [ -n "$BROWSER" ]; then
                "$BROWSER" http://localhost:3000 &
            fi
            echo ""
            echo "Press Enter to stop port-forward and continue..."
            read
            kill $GRAFANA_PID 2>/dev/null || true
            ;;
        7)
            echo ""
            echo -e "${BLUE}Prometheus Metrics:${NC}"
            echo "Fetching metrics from Spark application..."
            kubectl port-forward "$SPARK_POD" 8080:8080 > /dev/null 2>&1 &
            METRICS_PID=$!
            sleep 2
            curl -s http://localhost:8080/metrics 2>/dev/null | grep -E "spark_streaming|behavior" | head -20
            kill $METRICS_PID 2>/dev/null || true
            echo ""
            read -p "Press Enter to continue..."
            ;;
        8)
            echo ""
            echo -e "${GREEN}Monitoring all logs (Ctrl+C to stop):${NC}"
            echo ""
            kubectl logs -f "$SPARK_POD"
            ;;
        9)
            echo ""
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please select 1-9.${NC}"
            sleep 2
            ;;
    esac
    
    clear
    echo "User Behavior Classification - Live Monitor"
    echo "=============================================="
    echo ""
done
