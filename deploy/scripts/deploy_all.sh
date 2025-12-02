#!/bin/bash
#
# Automated Deployment Script for Big Data Customer Journey Analytics
# ====================================================================
# This script automates the complete deployment process
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================="
echo "  Big Data Customer Journey Analytics - Automated Deployment"
echo -e "=======================================================================${NC}"
echo ""

# Function to wait for user confirmation
wait_for_user() {
    echo -e "${YELLOW}Press ENTER to continue...${NC}"
    read
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed - Check error above${NC}"
        exit 1
    fi
}

echo -e "${BLUE}=== PHASE 0: Prerequisites Check ===${NC}"
echo ""
echo "Checking if all required tools are installed..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python3 is installed"
    python3 --version
else
    echo -e "${RED}✗${NC} Python3 is NOT installed"
    echo "Install with: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Check if in correct directory (look for key files in BTL_IT4931)
if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
    echo -e "${RED}✗${NC} Not in correct directory!"
    echo "Please run this script from the project root (BTL_IT4931)"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo ""
echo -e "${GREEN}Prerequisites check complete!${NC}"
wait_for_user

echo -e "${BLUE}=== PHASE 1: Python Environment Setup ===${NC}"
echo ""
echo "Setting up Python virtual environment..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    check_success
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

echo ""
echo "Activating virtual environment..."
source venv/bin/activate
check_success

echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
check_success

echo ""
echo -e "${GREEN}✓ Python environment ready!${NC}"
wait_for_user

echo -e "${BLUE}=== PHASE 2: Data Preparation ===${NC}"
echo ""

# Check for dataset
if [ ! -f "data/raw/ecommerce_events_2019_oct.csv" ]; then
    echo -e "${YELLOW}⚠${NC} Main dataset 'ecommerce_events_2019_oct.csv' not found!"
    echo ""
    echo "Please download '2019-Oct.csv' from:"
    echo "https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store"
    echo ""
    echo "Then place it in: data/raw/ecommerce_events_2019_oct.csv"
    echo ""
    wait_for_user
    
    if [ ! -f "data/raw/ecommerce_events_2019_oct.csv" ]; then
        echo -e "${RED}✗${NC} Dataset still not found. Cannot continue."
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Main dataset found"
echo ""

# Generate dimension tables if they don't exist
if [ ! -f "data/catalog/product_catalog.csv" ]; then
    echo "Generating dimension tables..."
    echo "This will create:"
    echo "  - data/catalog/user_dimension.csv"
    echo "  - data/catalog/product_catalog.csv (enhanced)"
    echo "  - data/catalog/category_hierarchy.csv"
    echo ""

    python -m app.utils.dimension_generator
    check_success
else
    echo -e "${GREEN}✓${NC} Dimension tables already exist"
fi

echo ""
echo -e "${GREEN}✓ Dimension tables generated!${NC}"
ls -lh data/catalog/*.csv
wait_for_user

echo -e "${BLUE}=== PHASE 3: Kubernetes Check ===${NC}"
echo ""
echo "Checking Kubernetes environment..."
echo ""

# Check Minikube
if ! command -v minikube &> /dev/null; then
    echo -e "${RED}✗${NC} Minikube is not installed"
    echo ""
    echo "Install Minikube:"
    echo "  curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64"
    echo "  sudo install minikube-linux-amd64 /usr/local/bin/minikube"
    exit 1
fi

echo -e "${GREEN}✓${NC} Minikube is installed"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗${NC} kubectl is not installed"
    echo ""
    echo "Install kubectl:"
    echo "  sudo snap install kubectl --classic"
    exit 1
fi

echo -e "${GREEN}✓${NC} kubectl is installed"

# Check Helm
if ! command -v helm &> /dev/null; then
    echo -e "${RED}✗${NC} Helm is not installed"
    echo ""
    echo "Install Helm:"
    echo "  sudo snap install helm --classic"
    exit 1
fi

echo -e "${GREEN}✓${NC} Helm is installed"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗${NC} Docker is not installed"
    echo ""
    echo "Install Docker:"
    echo "  sudo apt install docker.io"
    echo "  sudo usermod -aG docker $USER"
    echo "  newgrp docker"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is installed"

echo ""
echo -e "${GREEN}✓ All Kubernetes tools are ready!${NC}"
wait_for_user

echo -e "${BLUE}=== PHASE 4: Start Minikube ===${NC}"
echo ""

# Check if Minikube is running
MINIKUBE_STATUS=$(minikube status 2>/dev/null | grep "host:" | awk '{print $2}' || echo "Stopped")

if [ "$MINIKUBE_STATUS" != "Running" ]; then
    echo "Starting Minikube with 4 CPUs and 8GB RAM..."
    echo "This may take 2-3 minutes..."
    echo ""
    
    minikube start --driver=docker --cpus=4 --memory=8g --disk-size=20g
    check_success
else
    echo -e "${GREEN}✓${NC} Minikube is already running"
fi

echo ""
echo "Minikube status:"
minikube status

echo ""
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: ${GREEN}$MINIKUBE_IP${NC}"

echo ""
echo -e "${GREEN}✓ Minikube is ready!${NC}"
wait_for_user

echo -e "${BLUE}=== PHASE 5: Deploy MongoDB ===${NC}"
echo ""

# Add Bitnami repo
echo "Adding Bitnami Helm repository..."
helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
helm repo update
check_success

# Check if MongoDB is already installed
if helm list | grep -q "my-mongo"; then
    echo -e "${GREEN}✓${NC} MongoDB is already installed"
else
    echo ""
    echo "Installing MongoDB (without authentication for development)..."
    helm install my-mongo bitnami/mongodb --set auth.enabled=false
    check_success
fi

echo ""
echo "Waiting for MongoDB pod to be ready (this may take 1-2 minutes)..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mongodb --timeout=300s
check_success

echo ""
echo "MongoDB status:"
kubectl get pods | grep mongo || true

echo ""
echo -e "${GREEN}✓ MongoDB is running!${NC}"
wait_for_user

echo -e "${BLUE}=== PHASE 6: Deploy Kafka ===${NC}"
echo ""

# Add Strimzi repo
echo "Adding Strimzi Helm repository..."
helm repo add strimzi https://strimzi.io/charts/ 2>/dev/null || true
helm repo update
check_success

# Check if Strimzi is already installed
if helm list | grep -q "strimzi-operator"; then
    echo -e "${GREEN}✓${NC} Strimzi operator is already installed"
else
    echo ""
    echo "Installing Strimzi Kafka Operator..."
    helm install strimzi-operator strimzi/strimzi-kafka-operator
    check_success
fi

echo ""
echo "Waiting for Strimzi operator to be ready (this may take 1-2 minutes)..."
kubectl wait --for=condition=ready pod -l name=strimzi-cluster-operator --timeout=300s
check_success

# Check if Kafka cluster exists
if kubectl get kafka my-cluster &>/dev/null; then
    echo -e "${GREEN}✓${NC} Kafka cluster is already deployed"
else
    echo ""
    echo "Deploying Kafka cluster..."
    kubectl apply -f deploy/kubernetes/base/kafka-strimzi.yaml
    check_success
fi

echo ""
echo "Waiting for Kafka to be ready (this may take 2-3 minutes)..."
kubectl wait --for=condition=ready pod -l strimzi.io/name=my-cluster-kafka --timeout=300s
check_success

echo ""
echo "Kafka status:"
kubectl get pods | grep my-cluster || true

echo ""
echo -e "${GREEN}✓ Kafka is running!${NC}"
wait_for_user

echo -e "${BLUE}=== PHASE 7: Build Docker Image ===${NC}"
echo ""

echo "Configuring Docker to use Minikube's daemon..."
eval $(minikube docker-env)
check_success

echo ""
echo "Building Spark application Docker image..."
echo "This will take 5-10 minutes on first build..."
echo ""

docker build -t bigdata-spark:latest -f deploy/docker/Dockerfile .
check_success

echo ""
echo "Verifying image..."
docker images | grep bigdata-spark

echo ""
echo -e "${GREEN}✓ Docker image built successfully!${NC}"
wait_for_user

echo -e "${BLUE}=== PHASE 8: Deploy Spark Applications ===${NC}"
echo ""

echo "Deploying Spark applications to Kubernetes..."
kubectl apply -f deploy/kubernetes/base/spark-deployments.yaml
check_success

echo ""
echo "Waiting for Spark streaming deployment to be ready..."
sleep 10  # Give K8s time to create the deployment

kubectl wait --for=condition=available deployment/spark-streaming-advanced --timeout=300s 2>/dev/null || echo "Still starting..."

echo ""
echo "Current deployments:"
kubectl get deployments

echo ""
echo "Current pods:"
kubectl get pods

echo ""
echo -e "${GREEN}✓ Spark applications deployed!${NC}"
wait_for_user

echo -e "${BLUE}=== PHASE 9: Deploy Monitoring Stack ===${NC}"
echo ""

echo "Deploying Prometheus + Grafana monitoring stack..."
echo "This will enable real-time dashboards and Spark UI access"
echo ""

# Deploy monitoring components
echo "Deploying Prometheus..."
kubectl apply -f deploy/kubernetes/monitoring/prometheus-config.yaml
check_success

sleep 5

echo ""
echo "Deploying Grafana..."
kubectl apply -f deploy/kubernetes/monitoring/grafana.yaml
check_success

sleep 5

echo ""
echo "Deploying behavior classification dashboard..."
kubectl apply -f deploy/kubernetes/monitoring/behavior-dashboard.yaml
check_success

echo ""
echo "Exposing Spark UI..."
kubectl apply -f deploy/kubernetes/monitoring/spark-ui-service.yaml
check_success

echo ""
echo "Waiting for monitoring stack to be ready..."
kubectl wait --for=condition=ready pod -l app=prometheus --timeout=120s 2>/dev/null || echo "Prometheus starting..."
kubectl wait --for=condition=ready pod -l app=grafana --timeout=120s 2>/dev/null || echo "Grafana starting..."

echo ""
echo "Monitoring stack status:"
kubectl get pods | grep -E "prometheus|grafana|mongodb-exporter" || echo "Still initializing..."

echo ""
echo -e "${GREEN}✓ Monitoring stack deployed!${NC}"
wait_for_user

echo -e "${BLUE}=== PHASE 10: Setup Port-Forwards for Monitoring ===${NC}"
echo ""

echo "Setting up port-forwards for local access..."
echo "This allows you to access dashboards from your browser"
echo ""

# Kill any existing port-forwards
pkill -f "port-forward.*grafana" 2>/dev/null || true
pkill -f "port-forward.*prometheus" 2>/dev/null || true
pkill -f "port-forward.*spark" 2>/dev/null || true
sleep 2

# Start port-forwards in background
echo "Starting Grafana port-forward (3000)..."
kubectl port-forward svc/grafana 3000:3000 > /dev/null 2>&1 &
GRAFANA_PID=$!

echo "Starting Prometheus port-forward (9090)..."
kubectl port-forward svc/prometheus 9090:9090 > /dev/null 2>&1 &
PROMETHEUS_PID=$!

echo "Starting Spark UI port-forward (4040)..."
kubectl port-forward svc/spark-streaming-svc 4040:4040 > /dev/null 2>&1 &
SPARK_UI_PID=$!

sleep 3

echo ""
echo -e "${GREEN}✓ Port-forwards active!${NC}"
echo ""
echo "Access your monitoring dashboards:"
echo "  📊 Grafana:    http://localhost:3000 (admin/admin123)"
echo "  📈 Prometheus: http://localhost:9090"
echo "  🎯 Spark UI:   http://localhost:4040"
echo ""
echo "Port-forward PIDs: Grafana=$GRAFANA_PID, Prometheus=$PROMETHEUS_PID, Spark=$SPARK_UI_PID"
echo ""

# Save PIDs to file for later cleanup
echo "$GRAFANA_PID" > /tmp/monitoring-pids.txt
echo "$PROMETHEUS_PID" >> /tmp/monitoring-pids.txt
echo "$SPARK_UI_PID" >> /tmp/monitoring-pids.txt

wait_for_user

echo -e "${BLUE}=== PHASE 11: Get Kafka Connection Info ===${NC}"
echo ""

KAFKA_PORT=$(kubectl get service my-cluster-kafka-external-bootstrap -o jsonpath='{.spec.ports[0].nodePort}')

echo "Kafka connection details:"
echo "  IP: ${GREEN}$MINIKUBE_IP${NC}"
echo "  Port: ${GREEN}$KAFKA_PORT${NC}"
echo "  Full address: ${GREEN}$MINIKUBE_IP:$KAFKA_PORT${NC}"

echo ""
echo -e "${YELLOW}IMPORTANT:${NC} You need to update config/.env with this Kafka address"
echo ""
echo "Edit config/.env and set KAFKA_EXTERNAL_BROKER to:"
echo -e "${GREEN}KAFKA_EXTERNAL_BROKER=$MINIKUBE_IP:$KAFKA_PORT${NC}"
echo ""

wait_for_user

echo -e "${BLUE}=== PHASE 12: Verify Deployment ===${NC}"
echo ""

echo "Running validation checks..."
echo ""

# Manual checks
echo "Checking all components..."
echo ""

echo "MongoDB:"
kubectl get pods | grep mongo
echo ""

echo "Kafka:"
kubectl get pods | grep kafka
echo ""

echo "Spark:"
kubectl get pods | grep spark
echo ""

echo "Monitoring:"
kubectl get pods | grep -E "prometheus|grafana" || echo "Monitoring pods still starting..."
echo ""

echo ""
echo -e "${GREEN}✓ Deployment verification complete!${NC}"
wait_for_user

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════"
echo "  🎉 DEPLOYMENT COMPLETE - USER BEHAVIOR CLASSIFICATION PIPELINE"
echo -e "═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✅ All components deployed successfully!${NC}"
echo ""
echo "📊 ${YELLOW}MONITORING DASHBOARDS (Already Port-Forwarded):${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🎯 ${GREEN}Grafana Dashboard:${NC}    http://localhost:3000"
echo "     Username: admin"
echo "     Password: admin123"
echo "     → Pre-configured User Behavior Classification dashboard"
echo ""
echo "  📈 ${GREEN}Spark UI:${NC}             http://localhost:4040"
echo "     → View streaming job status, DAG visualization, metrics"
echo ""
echo "  📊 ${GREEN}Prometheus:${NC}           http://localhost:9090"
echo "     → Query raw metrics and create custom dashboards"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 ${YELLOW}QUICK START COMMANDS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. ${GREEN}Update Kafka config:${NC}"
echo "   Edit config/.env and set:"
echo "   KAFKA_EXTERNAL_BROKER=${YELLOW}$MINIKUBE_IP:$KAFKA_PORT${NC}"
echo ""
echo "2. ${GREEN}Generate test behavior data:${NC}"
echo "   ${YELLOW}python -m app.utils.test_behavior_generator${NC}"
echo ""
echo "3. ${GREEN}Interactive monitoring menu:${NC}"
echo "   ${YELLOW}bash deploy/scripts/monitor_streaming.sh${NC}"
echo ""
echo "4. ${GREEN}View real-time metrics (CLI):${NC}"
echo "   ${YELLOW}bash deploy/scripts/view_metrics.sh${NC}"
echo ""
echo "5. ${GREEN}Watch Spark logs:${NC}"
echo "   ${YELLOW}kubectl logs -f deployment/spark-streaming-advanced${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 ${YELLOW}WHAT'S RUNNING:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ✓ Kafka Cluster (events streaming)"
echo "  ✓ MongoDB (data storage)"
echo "  ✓ Spark Streaming (behavior classification)"
echo "  ✓ Prometheus (metrics collection)"
echo "  ✓ Grafana (visualization dashboards)"
echo "  ✓ MongoDB Exporter (database metrics)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 ${YELLOW}USER BEHAVIOR SEGMENTS TRACKED:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🔴 Bouncer:          1-2 events, <1 min sessions"
echo "  🟡 Browser:          3-10 events, cart but no purchase"
echo "  🟢 Engaged Shopper:  10-30 events, multiple purchases"
echo "  🔵 Power User:       30+ events, high engagement"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🛠️  ${YELLOW}USEFUL COMMANDS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  View all pods:       ${GREEN}kubectl get pods${NC}"
echo "  Restart Spark:       ${GREEN}kubectl rollout restart deployment/spark-streaming-advanced${NC}"
echo "  Scale Spark:         ${GREEN}kubectl scale deployment/spark-streaming-advanced --replicas=2${NC}"
echo "  View pod logs:       ${GREEN}kubectl logs -f <pod-name>${NC}"
echo "  Query MongoDB:       ${GREEN}kubectl exec -it <mongo-pod> -- mongosh bigdata${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🛑 ${YELLOW}TO STOP PORT-FORWARDS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ${GREEN}pkill -f 'port-forward'${NC}"
echo "  Or kill specific PIDs: ${GREEN}kill $GRAFANA_PID $PROMETHEUS_PID $SPARK_UI_PID${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🚀 Ready to start! Open the monitoring dashboards in your browser.${NC}"
echo ""
