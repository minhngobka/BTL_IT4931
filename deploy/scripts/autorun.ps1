#
# Automated Deployment Script for Big Data Customer Journey Analytics
# ====================================================================
# This script automates the complete deployment process for Windows
#

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[OK] $Message" "Green"
}

function Write-Error-Custom {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput $Message "Cyan"
}

Write-Info "======================================================================="
Write-Info "  Big Data Customer Journey Analytics - Automated Deployment"
Write-Info "======================================================================="
Write-Host ""

# Function to wait for user confirmation
function Wait-ForUser {
    Write-ColorOutput "Press ENTER to continue..." "Yellow"
    Read-Host
}

# Function to check command success
function Check-Success {
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Success"
    } else {
        Write-Error-Custom "Failed - Check error above"
        exit 1
    }
}

Write-Info "=== PHASE 0: Prerequisites Check ==="
Write-Host ""
Write-Host "Checking if all required tools are installed..."
Write-Host ""

# Check Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Success "Python is installed"
    python --version
} else {
    Write-Error-Custom "Python is NOT installed"
    Write-Host "Install from: https://www.python.org/downloads/"
    exit 1
}

# Check if in correct directory (look for key files in BTL_IT4931)
if (-not (Test-Path "requirements.txt") -or -not (Test-Path "app")) {
    Write-Error-Custom "Not in correct directory!"
    Write-Host "Please run this script from the project root (BTL_IT4931)"
    Write-Host "Current directory: $(Get-Location)"
    exit 1
}

Write-Host ""
Write-Success "Prerequisites check complete!"
Wait-ForUser

Write-Info "=== PHASE 1: Python Environment Setup ==="
Write-Host ""
Write-Host "Setting up Python virtual environment..."
Write-Host ""

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    Check-Success
} else {
    Write-Success "Virtual environment already exists"
}

Write-Host ""
Write-Host "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
    Write-Error-Custom "Failed to activate virtual environment"
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
    exit 1
}
Write-Success "Virtual environment activated"

Write-Host ""
Write-Host "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Check-Success

Write-Host ""
Write-Success "Python environment ready!"
Wait-ForUser

Write-Info "=== PHASE 2: Data Preparation ==="
Write-Host ""

# Check for dataset
if (-not (Test-Path "data\raw\ecommerce_events_2019_oct.csv")) {
    Write-Warning-Custom "Main dataset 'ecommerce_events_2019_oct.csv' not found!"
    Write-Host ""
    Write-Host "Please download '2019-Oct.csv' from:"
    Write-Host "https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store"
    Write-Host ""
    Write-Host "Then place it in: data\raw\ecommerce_events_2019_oct.csv"
    Write-Host ""
    Wait-ForUser
    
    if (-not (Test-Path "data\raw\ecommerce_events_2019_oct.csv")) {
        Write-Error-Custom "Dataset still not found. Cannot continue."
        exit 1
    }
}

Write-Success "Main dataset found"
Write-Host ""

# Generate dimension tables if they don't exist
if (-not (Test-Path "data\catalog\product_catalog.csv")) {
    Write-Host "Generating dimension tables..."
    Write-Host "This will create:"
    Write-Host "  - data\catalog\user_dimension.csv"
    Write-Host "  - data\catalog\product_catalog.csv (enhanced)"
    Write-Host "  - data\catalog\category_hierarchy.csv"
    Write-Host ""

    python -m app.utils.dimension_generator
    Check-Success
} else {
    Write-Success "Dimension tables already exist"
}

Write-Host ""
Write-Success "Dimension tables generated!"
Get-ChildItem "data\catalog\*.csv" | Format-Table Name, Length
Wait-ForUser

Write-Info "=== PHASE 3: Kubernetes Check ==="
Write-Host ""
Write-Host "Checking Kubernetes environment..."
Write-Host ""

# Check kubeadm
# if (-not (Get-Command kubeadm -ErrorAction SilentlyContinue)) {
#     Write-Error-Custom "kubeadm is not installed"
#     Write-Host ""
#     Write-Host "Install Kubernetes from:"
#     Write-Host "  https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/"
#     exit 1
# }

# Write-Success "kubeadm is installed"

# Check kubectl
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "kubectl is not installed"
    Write-Host ""
    Write-Host "Install kubectl from:"
    Write-Host "  https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
    Write-Host "Or use Chocolatey:"
    Write-Host "  choco install kubernetes-cli"
    exit 1
}

Write-Success "kubectl is installed"

# Check Helm
if (-not (Get-Command helm -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "Helm is not installed"
    Write-Host ""
    Write-Host "Install Helm from:"
    Write-Host "  https://helm.sh/docs/intro/install/"
    Write-Host "Or use Chocolatey:"
    Write-Host "  choco install kubernetes-helm"
    exit 1
}

Write-Success "Helm is installed"

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "Docker is not installed"
    Write-Host ""
    Write-Host "Install Docker Desktop from:"
    Write-Host "  https://www.docker.com/products/docker-desktop"
    exit 1
}

Write-Success "Docker is installed"

Write-Host ""
Write-Success "All Kubernetes tools are ready!"
Wait-ForUser

Write-Info "=== PHASE 4: Check Kubernetes Cluster ==="
Write-Host ""

# Check if kubectl can connect to cluster
Write-Host "Checking cluster connectivity..."
$clusterInfo = kubectl cluster-info 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Cannot connect to Kubernetes cluster"
    Write-Host ""
    Write-Host "Please ensure your Kubernetes cluster is running and kubectl is configured."
    Write-Host "If you haven't initialized your cluster yet, run:"
    Write-Host "  kubeadm init"
    exit 1
}

Write-Host ""
Write-Host "Cluster status:"
kubectl cluster-info

Write-Host ""
# Get cluster IP (use localhost for kubeadm single-node or get node IP)
$nodeIp = kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"InternalIP\")].address}'
if (-not $nodeIp) {
    $nodeIp = "localhost"
}
Write-ColorOutput "Cluster Node IP: $nodeIp" "Green"

Write-Host ""
Write-Success "Kubernetes cluster is ready!"
Wait-ForUser

Write-Info "=== PHASE 5: Deploy MongoDB ==="
Write-Host ""

# Add Bitnami repo
Write-Host "Adding Bitnami Helm repository..."
helm repo add bitnami https://charts.bitnami.com/bitnami 2>$null
helm repo update
Check-Success

# Check if MongoDB is already installed
$mongoInstalled = helm list | Select-String "my-mongo"
if ($mongoInstalled) {
    Write-Success "MongoDB is already installed"
} else {
    Write-Host ""
    Write-Host "Installing MongoDB (without authentication for development)..."
    helm install my-mongo bitnami/mongodb --set auth.enabled=false
    Check-Success
}

Write-Host ""
Write-Host "Waiting for MongoDB pod to be ready (this may take 1-2 minutes)..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mongodb --timeout=300s
Check-Success

Write-Host ""
Write-Host "MongoDB status:"
kubectl get pods | Select-String "mongo"

Write-Host ""
Write-Success "MongoDB is running!"
Wait-ForUser

Write-Info "=== PHASE 6: Deploy Kafka ==="
Write-Host ""

# Add Strimzi repo
Write-Host "Adding Strimzi Helm repository..."
helm repo add strimzi https://strimzi.io/charts/ 2>$null
helm repo update
Check-Success

# Check if Strimzi is already installed
$strimziInstalled = helm list | Select-String "strimzi-operator"
if ($strimziInstalled) {
    Write-Success "Strimzi operator is already installed"
} else {
    Write-Host ""
    Write-Host "Installing Strimzi Kafka Operator..."
    helm install strimzi-operator strimzi/strimzi-kafka-operator
    Check-Success
}

Write-Host ""
Write-Host "Waiting for Strimzi operator to be ready (this may take 1-2 minutes)..."
kubectl wait --for=condition=ready pod -l name=strimzi-cluster-operator --timeout=300s
Check-Success

# Check if Kafka cluster exists
$kafkaExists = kubectl get kafka my-cluster --ignore-not-found -o name
if ($kafkaExists) {
    Write-Success "Kafka cluster is already deployed"
} else {
    Write-Host ""
    Write-Host "Deploying Kafka cluster..."
    kubectl apply -f deploy\kubernetes\base\kafka-strimzi.yaml
    Check-Success
}

Write-Host ""
Write-Host "Waiting for Kafka to be ready (this may take 2-3 minutes)..."
kubectl wait --for=condition=ready pod -l strimzi.io/name=my-cluster-kafka --timeout=300s
Check-Success

Write-Host ""
Write-Host "Kafka status:"
kubectl get pods | Select-String "my-cluster"

Write-Host ""
Write-Success "Kafka is running!"
Wait-ForUser

Write-Info "=== PHASE 7: Build Docker Image ==="
Write-Host ""

Write-Host "Building Spark application Docker image..."
Write-Host "This will take 5-10 minutes on first build..."
Write-Host "Note: Image will be pushed to Docker Hub or local registry for kubeadm to access"
Write-Host ""

docker build -t huynambka/bigdata-spark:latest -f deploy\docker\Dockerfile .
Check-Success

docker push huynambka/bigdata-spark:latest
Check-Success

Write-Host ""
Write-Host "Verifying image..."
docker images | Select-String "bigdata-spark"

Write-Host ""
Write-Success "Docker image built successfully!"
Wait-ForUser

Write-Info "=== PHASE 8: Deploy Spark Applications ==="
Write-Host ""

Write-Host "Deploying Spark applications to Kubernetes..."
kubectl apply -f deploy\kubernetes\base\spark-deployments.yaml
Check-Success

Write-Host ""
Write-Host "Waiting for Spark streaming deployment to be ready..."
Start-Sleep -Seconds 10

kubectl wait --for=condition=available deployment.apps/spark-streaming-with-pvc --timeout=300s 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Still starting..."
}

Write-Host ""
Write-Host "Current deployments:"
kubectl get deployments

Write-Host ""
Write-Host "Current pods:"
kubectl get pods

Write-Host ""
Write-Success "Spark applications deployed!"
Wait-ForUser

Write-Info "=== PHASE 10: Setup Port-Forwards for Spark UI ==="
Write-Host ""

Write-Host "Setting up port-forwards for local access..."
Write-Host "This allows you to access Spark UI from your browser"
Write-Host ""

# Kill any existing port-forwards
Get-Process | Where-Object { $_.ProcessName -eq "kubectl" -and $_.CommandLine -like "*port-forward*spark*" } | Stop-Process -Force 2>$null
Start-Sleep -Seconds 2

# Start port-forwards in background
Write-Host "Starting Spark UI port-forward (4040)..."
$sparkJob = Start-Job -ScriptBlock { kubectl port-forward svc/spark-streaming-svc 4040:4040 }
$sparkUiPid = $sparkJob.Id

Start-Sleep -Seconds 3

Write-Host ""
Write-Success "Port-forwards active!"
Write-Host ""
Write-Host "Access your Spark UI:"
Write-Host "  [*] Spark UI:   http://localhost:4040"
Write-Host ""
Write-Host "Port-forward Job ID: Spark=$sparkUiPid"
Write-Host ""

# Save job IDs to file for later cleanup
"$sparkUiPid" | Out-File -FilePath "$env:TEMP\monitoring-jobs.txt"

Wait-ForUser

Write-Info "=== PHASE 11: Get Kafka Connection Info ==="
Write-Host ""

$kafkaPort = kubectl get service my-cluster-kafka-external-bootstrap -o jsonpath='{.spec.ports[0].nodePort}'

Write-Host "Kafka connection details:"
Write-ColorOutput "  IP: $nodeIp" "Green"
Write-ColorOutput "  Port: $kafkaPort" "Green"
Write-ColorOutput "  Full address: $nodeIp`:$kafkaPort" "Green"

Write-Host ""
Write-Warning-Custom "IMPORTANT: You need to update config\.env with this Kafka address"
Write-Host ""
Write-Host "Edit config\.env and set KAFKA_EXTERNAL_BROKER to:"
Write-ColorOutput "KAFKA_EXTERNAL_BROKER=$nodeIp`:$kafkaPort" "Green"
Write-Host ""

Wait-ForUser

Write-Info "=== PHASE 11: Deploy Monitoring Stack ==="
Write-Host ""

# Add Helm repositories
Write-Host "Adding Helm repositories..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>$null
helm repo update
Check-Success

# Check if Prometheus stack is already installed
$prometheusInstalled = helm list | Select-String "prometheus"
if ($prometheusInstalled) {
    Write-Success "Prometheus stack is already installed"
} else {
    Write-Host ""
    Write-Host "Installing Prometheus & Grafana stack..."
    Write-Host "This includes Prometheus, Grafana, and Alertmanager"
    helm install prometheus prometheus-community/kube-prometheus-stack
    Check-Success
}

Write-Host ""
Write-Host "Waiting for Prometheus pods to be ready (this may take 2-3 minutes)..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana --timeout=300s 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Still starting..."
}

# Check if MongoDB exporter is already installed
$mongoExporterInstalled = helm list | Select-String "mongo-exporter"
if ($mongoExporterInstalled) {
    Write-Success "MongoDB exporter is already installed"
} else {
    Write-Host ""
    Write-Host "Installing MongoDB exporter..."
    helm install mongo-exporter prometheus-community/prometheus-mongodb-exporter -f .\deploy\kubernetes\base\mongo-exporter-values.yaml
    Check-Success
}

Write-Host ""
Write-Host "Upgrading Prometheus with custom Grafana configuration..."
helm upgrade prometheus prometheus-community/kube-prometheus-stack -f config\grafana-values.yaml
Check-Success

Write-Host ""
Write-Host "Getting Grafana admin password..."
$grafanaPasswordBytes = kubectl --namespace default get secrets prometheus-grafana -o jsonpath="{.data.admin-password}"
$grafanaPassword = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($grafanaPasswordBytes))
Write-ColorOutput "Grafana Password: $grafanaPassword" "Green"

Write-Host ""
Write-Host "Setting up Grafana port-forward (3000)..."
Get-Process | Where-Object { $_.ProcessName -eq "kubectl" -and $_.CommandLine -like "*port-forward*grafana*" } | Stop-Process -Force 2>$null
Start-Sleep -Seconds 2
$grafanaJob = Start-Job -ScriptBlock { kubectl port-forward svc/prometheus-grafana 3000:80 }
$grafanaPid = $grafanaJob.Id
Write-Host "Grafana port-forward Job ID: $grafanaPid"

Write-Host ""
Write-Success "Monitoring stack deployed!"
Write-Host "  [*] Grafana: http://localhost:3000 (admin/$grafanaPassword)"
Write-Host "  [*] Prometheus: Available via Grafana"
Write-Host "  [*] MongoDB Exporter: Collecting metrics"

Wait-ForUser

Write-Info "=== PHASE 12: Deploy Metabase ==="
Write-Host ""

Write-Host "Deploying Metabase for business intelligence..."
kubectl apply -f deploy\kubernetes\base\metabase.yaml
Check-Success

Write-Host ""
Write-Host "Waiting for Metabase pod to be ready (this may take 2-3 minutes)..."
kubectl wait --for=condition=ready pod -l app=metabase --timeout=300s 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Still starting..."
}

Write-Host ""
Write-Host "Setting up Metabase port-forward (3001)..."
Get-Process | Where-Object { $_.ProcessName -eq "kubectl" -and $_.CommandLine -like "*port-forward*metabase*" } | Stop-Process -Force 2>$null
Start-Sleep -Seconds 2
$metabaseJob = Start-Job -ScriptBlock { kubectl port-forward svc/metabase-service 3001:3000 }
$metabasePid = $metabaseJob.Id
Write-Host "Metabase port-forward Job ID: $metabasePid"

Write-Host ""
Write-Success "Metabase deployed!"
Write-Host "  [*] Metabase UI: http://localhost:3001"
Write-Host "  [*] Connect to MongoDB: mongodb://my-mongo-mongodb.default.svc.cluster.local:27017"

Wait-ForUser

Write-Info "=== PHASE 13: Verify Deployment ==="
Write-Host ""

Write-Host "Running validation checks..."
Write-Host ""

# Manual checks
Write-Host "Checking all components..."
Write-Host ""

Write-Host "1. MongoDB:"
kubectl get pods | Select-String "mongo"
Write-Host ""

Write-Host "2. Kafka:"
kubectl get pods | Select-String "kafka"
Write-Host ""

Write-Host "3. Spark:"
kubectl get pods | Select-String "spark"
Write-Host ""

Write-Host "4. Monitoring (Prometheus/Grafana):"
kubectl get pods | Select-String -Pattern "prometheus|grafana"
Write-Host ""

Write-Host "5. Metabase:"
kubectl get pods | Select-String "metabase"
Write-Host ""

Write-Host "6. Services:"
kubectl get svc | Select-String -Pattern "mongo|kafka|spark|grafana|metabase"
Write-Host ""

Write-Host "7. Port-forwards active:"
Get-Job | Where-Object { $_.State -eq "Running" } | Format-Table Id, Name, State
Write-Host ""

Write-Host ""
Write-Success "Deployment verification complete!"
Wait-ForUser

Write-Host ""
Write-Info "======================================================================="
Write-Info "  DEPLOYMENT COMPLETE - USER BEHAVIOR CLASSIFICATION PIPELINE"
Write-Info "======================================================================="
Write-Host ""
Write-Success "All components deployed successfully!"
Write-Host ""
Write-ColorOutput "ACCESS DASHBOARDS:" "Yellow"
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "  [*] Spark UI:             http://localhost:4040" "Green"
Write-Host "      -> View streaming job status, DAG visualization, metrics"
Write-Host ""
Write-ColorOutput "  [*] Grafana:              http://localhost:3000" "Green"
Write-Host "      -> Username: admin | Password: $grafanaPassword"
Write-Host "      -> MongoDB metrics, system monitoring, custom dashboards"
Write-Host ""
Write-ColorOutput "  [*] Metabase:             http://localhost:3001" "Green"
Write-Host "      -> Business intelligence and data exploration"
Write-Host "      -> MongoDB: mongodb://my-mongo-mongodb.default.svc.cluster.local:27017"
Write-Host ""
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "QUICK START COMMANDS:" "Yellow"
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "1. Update Kafka config:" "Green"
Write-Host "   Edit config\.env and set:"
Write-ColorOutput "   KAFKA_EXTERNAL_BROKER=$nodeIp`:$kafkaPort" "Yellow"
Write-Host ""
Write-ColorOutput "2. Generate test behavior data:" "Green"
Write-ColorOutput "   python -m app.utils.test_behavior_generator" "Yellow"
Write-Host ""
Write-ColorOutput "3. Interactive monitoring menu:" "Green"
Write-ColorOutput "   powershell .\deploy\scripts\monitor_streaming.ps1" "Yellow"
Write-Host ""
Write-ColorOutput "4. View real-time metrics (CLI):" "Green"
Write-ColorOutput "   powershell .\deploy\scripts\view_metrics.ps1" "Yellow"
Write-Host ""
Write-ColorOutput "5. Watch Spark logs:" "Green"
Write-ColorOutput "   kubectl logs -f deployment/spark-streaming-advanced" "Yellow"
Write-Host ""
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "WHAT'S RUNNING:" "Yellow"
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-Host "  [*] Kafka Cluster (events streaming)"
Write-Host "  [*] MongoDB (data storage)"
Write-Host "  [*] Spark Streaming (behavior classification)"
Write-Host "  [*] Prometheus + Grafana (monitoring & visualization)"
Write-Host "  [*] MongoDB Exporter (metrics collection)"
Write-Host "  [*] Metabase (business intelligence)"
Write-Host ""
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "USER BEHAVIOR SEGMENTS TRACKED:" "Yellow"
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-Host "  [RED] Bouncer:          1-2 events, less than 1 min sessions"
Write-Host "  [YELLOW] Browser:       3-10 events, cart but no purchase"
Write-Host "  [GREEN] Engaged Shopper:  10-30 events, multiple purchases"
Write-Host "  [BLUE] Power User:      30+ events, high engagement"
Write-Host ""
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "USEFUL COMMANDS:" "Yellow"
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "  View all pods:       kubectl get pods" "Green"
Write-ColorOutput "  Restart Spark:       kubectl rollout restart deployment/spark-streaming-advanced" "Green"
Write-ColorOutput "  Scale Spark:         kubectl scale deployment/spark-streaming-advanced --replicas=2" "Green"
Write-ColorOutput "  View pod logs:       kubectl logs -f [pod-name]" "Green"
Write-ColorOutput "  Query MongoDB:       kubectl exec -it [mongo-pod] -- mongosh bigdata" "Green"
Write-Host ""
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "TO STOP PORT-FORWARDS:" "Yellow"
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "  Get-Job | Stop-Job" "Green"
Write-Host "  Or stop specific jobs:"
Write-ColorOutput "    Spark UI:  Stop-Job -Id $sparkUiPid" "Green"
Write-ColorOutput "    Grafana:   Stop-Job -Id $grafanaPid" "Green"
Write-ColorOutput "    Metabase:  Stop-Job -Id $metabasePid" "Green"
Write-Host ""
Write-Host "----------------------------------------------------------------------"
Write-Host ""
Write-ColorOutput "Ready to start! Open the monitoring dashboards in your browser." "Green"
Write-Host ""
