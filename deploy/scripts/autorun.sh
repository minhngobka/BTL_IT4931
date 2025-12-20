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

docker build -t huynambka/bigdata-spark:latest -f deploy/docker/Dockerfile .
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

kubectl wait --for=condition=available deployment.apps/spark-streaming-with-pvc --timeout=300s 2>/dev/null || echo "Still starting..."

echo ""
echo "Current deployments:"
kubectl get deployments

echo ""
echo "Current pods:"
kubectl get pods

echo ""
echo -e "${GREEN}✓ Spark applications deployed!${NC}"
wait_for_user



echo -e "${BLUE}=== PHASE 10: Setup Port-Forwards for Spark UI ===${NC}"
echo ""

echo "Setting up port-forwards for local access..."
echo "This allows you to access Spark UI from your browser"
echo ""

# Kill any existing port-forwards
pkill -f "port-forward.*spark" 2>/dev/null || true
sleep 2

# Start port-forwards in background
echo "Starting Spark UI port-forward (4040)..."
kubectl port-forward svc/spark-streaming-svc 4040:4040 > /dev/null 2>&1 &
SPARK_UI_PID=$!

sleep 3

echo ""
echo -e "${GREEN}✓ Port-forwards active!${NC}"
echo ""
echo "Access your Spark UI:"
echo "  🎯 Spark UI:   http://localhost:4040"
echo ""
echo "Port-forward PID: Spark=$SPARK_UI_PID"
echo ""

# Save PIDs to file for later cleanup
echo "$SPARK_UI_PID" > /tmp/monitoring-pids.txt

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

# echo -e "${BLUE}=== PHASE 11: Deploy Monitoring Stack ===${NC}"
# echo ""

# # Add Helm repositories
# echo "Adding Helm repositories..."
# helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
# helm repo update
# check_success

# # Check if Prometheus stack is already installed
# if helm list | grep -q "prometheus"; then
#     echo -e "${GREEN}✓${NC} Prometheus stack is already installed"
# else
#     echo ""
#     echo "Installing Prometheus & Grafana stack..."
#     echo "This includes Prometheus, Grafana, and Alertmanager"
#     helm install prometheus prometheus-community/kube-prometheus-stack
#     check_success
# fi

# echo ""
# echo "Waiting for Prometheus pods to be ready (this may take 2-3 minutes)..."
# kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana --timeout=300s 2>/dev/null || echo "Still starting..."

# # Check if MongoDB exporter is already installed
# if helm list | grep -q "mongo-exporter"; then
#     echo -e "${GREEN}✓${NC} MongoDB exporter is already installed"
# else
#     echo ""
#     echo "Installing MongoDB exporter..."
#     helm install mongo-exporter prometheus-community/prometheus-mongodb-exporter \
#       -f ./deploy/kubernetes/base/mongo-exporter-values.yaml
#     check_success
# fi

# echo ""
# echo "Upgrading Prometheus with custom Grafana configuration..."
# helm upgrade prometheus prometheus-community/kube-prometheus-stack -f config/grafana-values.yaml
# check_success

# echo ""
# echo "Getting Grafana admin password..."
# GRAFANA_PASSWORD=$(kubectl --namespace default get secrets prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d)
# echo -e "Grafana Password: ${GREEN}$GRAFANA_PASSWORD${NC}"

# echo ""
# echo "Setting up Grafana port-forward (3000)..."
# pkill -f "port-forward.*grafana" 2>/dev/null || true
# sleep 2
# kubectl port-forward svc/prometheus-grafana 3000:80 > /dev/null 2>&1 &
# GRAFANA_PID=$!
# echo "Grafana port-forward PID: $GRAFANA_PID"

# echo ""
# echo -e "${GREEN}✓ Monitoring stack deployed!${NC}"
# echo "  🔹 Grafana: http://localhost:3000 (admin/$GRAFANA_PASSWORD)"
# echo "  🔹 Prometheus: Available via Grafana"
# echo "  🔹 MongoDB Exporter: Collecting metrics"

# wait_for_user

echo -e "${BLUE}=== PHASE 12: Deploy Metabase ===${NC}"
echo ""

echo "Deploying Metabase for business intelligence..."
kubectl apply -f deploy/kubernetes/base/metabase.yaml
check_success

echo ""
echo "Waiting for Metabase pod to be ready (this may take 2-3 minutes)..."
kubectl wait --for=condition=ready pod -l app=metabase --timeout=300s 2>/dev/null || echo "Still starting..."

echo ""
echo "Setting up Metabase port-forward (3001)..."
pkill -f "port-forward.*metabase" 2>/dev/null || true
sleep 2
kubectl port-forward svc/metabase-service 3001:3000 > /dev/null 2>&1 &
METABASE_PID=$!
echo "Metabase port-forward PID: $METABASE_PID"

echo ""
echo -e "${GREEN}✓ Metabase deployed!${NC}"
echo "  🔹 Metabase UI: http://localhost:3001"
echo "  🔹 Connect to MongoDB: mongodb://my-mongo-mongodb.default.svc.cluster.local:27017"

wait_for_user

echo -e "${BLUE}=== PHASE 13: Verify Deployment ===${NC}"
echo ""

echo "Running validation checks..."
echo ""

# Manual checks
echo "Checking all components..."
echo ""

echo "1. MongoDB:"
kubectl get pods | grep mongo || echo "  No MongoDB pods found!"
echo ""

echo "2. Kafka:"
kubectl get pods | grep kafka || echo "  No Kafka pods found!"
echo ""

echo "3. Spark:"
kubectl get pods | grep spark || echo "  No Spark pods found!"
echo ""

echo "4. Monitoring (Prometheus/Grafana):"
kubectl get pods | grep -E "prometheus|grafana" || echo "  No monitoring pods found!"
echo ""

echo "5. Metabase:"
kubectl get pods | grep metabase || echo "  No Metabase pods found!"
echo ""

echo "6. Services:"
kubectl get svc | grep -E "mongo|kafka|spark|grafana|metabase" || echo "  No services found!"
echo ""

echo "7. Port-forwards active:"
ps aux | grep -E "port-forward.*(3000|3001|4040)" | grep -v grep || echo "  No port-forwards active"
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
echo "📊 ${YELLOW}ACCESS DASHBOARDS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📈 ${GREEN}Spark UI:${NC}             http://localhost:4040"
echo "     → View streaming job status, DAG visualization, metrics"
echo ""
echo "  📊 ${GREEN}Grafana:${NC}              http://localhost:3000"
echo "     → Username: admin | Password: $GRAFANA_PASSWORD"
echo "     → MongoDB metrics, system monitoring, custom dashboards"
echo ""
echo "  💼 ${GREEN}Metabase:${NC}             http://localhost:3001"
echo "     → Business intelligence and data exploration"
echo "     → MongoDB: mongodb://my-mongo-mongodb.default.svc.cluster.local:27017"
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
echo "  ✓ Prometheus + Grafana (monitoring & visualization)"
echo "  ✓ MongoDB Exporter (metrics collection)"
echo "  ✓ Metabase (business intelligence)"
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
echo "  Or kill specific PIDs:"
echo "    Spark UI:  ${GREEN}kill $SPARK_UI_PID${NC}"
echo "    Grafana:   ${GREEN}kill $GRAFANA_PID${NC}"
echo "    Metabase:  ${GREEN}kill $METABASE_PID${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🚀 Ready to start! Open the monitoring dashboards in your browser.${NC}"
echo ""
