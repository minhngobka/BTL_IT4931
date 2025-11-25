#!/bin/bash

# Validation Script for Big Data Project
# This script checks if all components are properly deployed and running

echo "=========================================="
echo "Big Data Project - System Validation"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 NOT found"
        return 1
    fi
}

check_pod() {
    POD_NAME=$1
    STATUS=$(kubectl get pods 2>/dev/null | grep $POD_NAME | awk '{print $3}')
    if [ "$STATUS" == "Running" ]; then
        echo -e "${GREEN}✓${NC} $POD_NAME is Running"
        return 0
    elif [ -z "$STATUS" ]; then
        echo -e "${RED}✗${NC} $POD_NAME NOT found"
        return 1
    else
        echo -e "${YELLOW}⚠${NC} $POD_NAME status: $STATUS"
        return 1
    fi
}

# Phase 1: Check Prerequisites
echo "Phase 1: Checking Prerequisites"
echo "--------------------------------"

ALL_GOOD=true

check_command docker || ALL_GOOD=false
check_command kubectl || ALL_GOOD=false
check_command minikube || ALL_GOOD=false
check_command helm || ALL_GOOD=false
check_command python3 || ALL_GOOD=false

echo ""

# Phase 2: Check Minikube
echo "Phase 2: Checking Minikube"
echo "--------------------------"

MINIKUBE_STATUS=$(minikube status 2>/dev/null | grep "host:" | awk '{print $2}')
if [ "$MINIKUBE_STATUS" == "Running" ]; then
    echo -e "${GREEN}✓${NC} Minikube is Running"
    MINIKUBE_IP=$(minikube ip 2>/dev/null)
    echo "  Minikube IP: $MINIKUBE_IP"
else
    echo -e "${RED}✗${NC} Minikube is NOT running"
    echo "  Run: minikube start --driver=docker --cpus=4 --memory=8g"
    ALL_GOOD=false
fi

echo ""

# Phase 3: Check Required Files
echo "Phase 3: Checking Required Files"
echo "--------------------------------"

check_file "2019-Oct.csv" || echo "  Download from: https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store"
check_file "product_catalog.csv" || echo "  Run: python generate_dimensions.py"
check_file "user_dimension.csv" || echo "  Run: python generate_dimensions.py"
check_file "streaming_app_advanced.py" || ALL_GOOD=false
check_file "batch_analytics_ml.py" || ALL_GOOD=false
check_file "Dockerfile" || ALL_GOOD=false
check_file "kafka-combined.yaml" || ALL_GOOD=false
check_file "k8s-spark-apps.yaml" || ALL_GOOD=false
check_file "requirements.txt" || ALL_GOOD=false

echo ""

# Phase 4: Check Kubernetes Resources
echo "Phase 4: Checking Kubernetes Deployments"
echo "---------------------------------------"

# Check if kubectl can connect
kubectl cluster-info &> /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} kubectl can connect to cluster"
else
    echo -e "${RED}✗${NC} kubectl cannot connect to cluster"
    ALL_GOOD=false
fi

# Check pods
check_pod "my-mongo-mongodb"
MONGO_STATUS=$?

check_pod "my-cluster-kafka-0"
KAFKA_STATUS=$?

check_pod "strimzi-cluster-operator"
STRIMZI_STATUS=$?

check_pod "spark-streaming-advanced"
SPARK_STATUS=$?

echo ""

# Phase 5: Check Docker Image
echo "Phase 5: Checking Docker Image"
echo "------------------------------"

eval $(minikube docker-env 2>/dev/null)
if docker images | grep -q "bigdata-spark"; then
    echo -e "${GREEN}✓${NC} bigdata-spark image exists"
    IMAGE_SIZE=$(docker images bigdata-spark:latest --format "{{.Size}}")
    echo "  Image size: $IMAGE_SIZE"
else
    echo -e "${RED}✗${NC} bigdata-spark image NOT found"
    echo "  Run: eval \$(minikube docker-env) && docker build -t bigdata-spark:latest ."
    ALL_GOOD=false
fi

echo ""

# Phase 6: Check Services
echo "Phase 6: Checking Services"
echo "-------------------------"

# Check Kafka service
KAFKA_PORT=$(kubectl get service my-cluster-kafka-external-bootstrap -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
if [ ! -z "$KAFKA_PORT" ]; then
    echo -e "${GREEN}✓${NC} Kafka service exists"
    echo "  Kafka NodePort: $KAFKA_PORT"
    if [ ! -z "$MINIKUBE_IP" ]; then
        echo "  Kafka Address: $MINIKUBE_IP:$KAFKA_PORT"
    fi
else
    echo -e "${RED}✗${NC} Kafka service NOT found"
    ALL_GOOD=false
fi

# Check MongoDB service
MONGO_SERVICE=$(kubectl get service my-mongo-mongodb -o jsonpath='{.metadata.name}' 2>/dev/null)
if [ ! -z "$MONGO_SERVICE" ]; then
    echo -e "${GREEN}✓${NC} MongoDB service exists"
else
    echo -e "${RED}✗${NC} MongoDB service NOT found"
    ALL_GOOD=false
fi

echo ""

# Phase 7: Check Helm Releases
echo "Phase 7: Checking Helm Releases"
echo "-------------------------------"

if helm list | grep -q "my-mongo"; then
    echo -e "${GREEN}✓${NC} MongoDB Helm release exists"
else
    echo -e "${RED}✗${NC} MongoDB Helm release NOT found"
    echo "  Run: helm install my-mongo bitnami/mongodb --set auth.enabled=false"
fi

if helm list | grep -q "strimzi-operator"; then
    echo -e "${GREEN}✓${NC} Strimzi Helm release exists"
else
    echo -e "${RED}✗${NC} Strimzi Helm release NOT found"
    echo "  Run: helm install strimzi-operator strimzi/strimzi-kafka-operator"
fi

echo ""

# Phase 8: Quick Health Check
echo "Phase 8: Component Health Check"
echo "-------------------------------"

if [ $MONGO_STATUS -eq 0 ]; then
    # Try to connect to MongoDB
    kubectl exec -it my-mongo-mongodb-0 -- mongosh --eval "db.adminCommand('ping')" &> /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} MongoDB is healthy and responding"
    else
        echo -e "${YELLOW}⚠${NC} MongoDB pod running but not responding"
    fi
fi

if [ $KAFKA_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Kafka pod is running (check logs for detailed status)"
fi

if [ $SPARK_STATUS -eq 0 ]; then
    # Check if streaming app has errors
    ERROR_COUNT=$(kubectl logs deployment/spark-streaming-advanced 2>/dev/null | grep -i error | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠${NC} Spark streaming has $ERROR_COUNT errors in logs"
    else
        echo -e "${GREEN}✓${NC} Spark streaming appears healthy"
    fi
fi

echo ""

# Phase 9: Data Validation
echo "Phase 9: Data Validation"
echo "-----------------------"

if [ $MONGO_STATUS -eq 0 ]; then
    ENRICHED_COUNT=$(kubectl exec -it my-mongo-mongodb-0 -- mongosh bigdata_db --quiet --eval "db.enriched_events.countDocuments()" 2>/dev/null | tail -1)
    
    if [ ! -z "$ENRICHED_COUNT" ] && [ "$ENRICHED_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Data exists in MongoDB"
        echo "  Enriched events: $ENRICHED_COUNT"
    else
        echo -e "${YELLOW}⚠${NC} No data in MongoDB yet"
        echo "  Make sure simulator.py is running"
    fi
fi

echo ""

# Final Summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="

if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All critical components are ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Update simulator.py with Kafka address: $MINIKUBE_IP:$KAFKA_PORT"
    echo "2. Run simulator: python simulator.py"
    echo "3. Monitor logs: kubectl logs -f deployment/spark-streaming-advanced"
    echo "4. Access Spark UI: kubectl port-forward deployment/spark-streaming-advanced 4040:4040"
    echo "5. Run batch job: kubectl create job spark-batch-manual --from=cronjob/spark-batch-ml-scheduled"
else
    echo -e "${RED}✗ Some components need attention${NC}"
    echo ""
    echo "Please fix the issues marked with ✗ above"
    echo "Refer to DEPLOYMENT_GUIDE.md for detailed instructions"
fi

echo ""
echo "For detailed logs:"
echo "  kubectl get pods                           # List all pods"
echo "  kubectl logs <pod-name>                    # View pod logs"
echo "  kubectl describe pod <pod-name>            # Detailed pod info"
echo "  kubectl get events --sort-by='.lastTimestamp'  # Recent events"
echo ""

exit 0
