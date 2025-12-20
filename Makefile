.PHONY: help install build test clean deploy run-simulator run-streaming run-ml

# Variables
PYTHON := python3
PIP := pip3
DOCKER := docker
KUBECTL := kubectl
MINIKUBE := minikube

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install Python dependencies
	@echo "$(GREEN)Installing Python dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

install-dev: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov black flake8 mypy pylint

format: ## Format code with black
	@echo "$(GREEN)Formatting code...$(NC)"
	black app/ tests/

lint: ## Run linters
	@echo "$(GREEN)Running linters...$(NC)"
	flake8 app/ --max-line-length=120 --ignore=E203,W503
	pylint app/ --disable=C0111,C0103

test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

# Docker targets
build-docker: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	eval $$($(MINIKUBE) docker-env) && \
	$(DOCKER) build -t bigdata-spark:latest -f deploy/docker/Dockerfile .

load-docker: build-docker ## Build and load Docker image to Minikube
	@echo "$(GREEN)Loading image to Minikube...$(NC)"
	$(MINIKUBE) image load bigdata-spark:latest

# Kubernetes targets
deploy-kafka: ## Deploy Kafka cluster
	@echo "$(GREEN)Deploying Kafka...$(NC)"
	$(KUBECTL) create namespace kafka 2>/dev/null || true
	$(KUBECTL) apply -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
	$(KUBECTL) apply -f deploy/kubernetes/base/kafka-strimzi.yaml

deploy-mongodb: ## Deploy MongoDB
	@echo "$(GREEN)Deploying MongoDB...$(NC)"
	helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
	helm repo update
	helm upgrade --install my-mongo bitnami/mongodb \
	  --set auth.enabled=false \
	  --set persistence.size=5Gi \
	  --wait --timeout=10m

deploy-spark: ## Deploy Spark applications
	@echo "$(GREEN)Deploying Spark applications...$(NC)"
	$(KUBECTL) apply -f deploy/kubernetes/base/spark-deployments.yaml

deploy: deploy-kafka deploy-mongodb load-docker deploy-spark ## Deploy all components
	@echo "$(GREEN)Deployment complete!$(NC)"

undeploy: ## Remove all deployments
	@echo "$(YELLOW)Removing all deployments...$(NC)"
	$(KUBECTL) delete -f deploy/kubernetes/base/spark-deployments.yaml 2>/dev/null || true
	$(KUBECTL) delete -f deploy/kubernetes/base/kafka-strimzi.yaml 2>/dev/null || true
	helm uninstall my-mongo 2>/dev/null || true

# Run targets
run-simulator: ## Run event simulator
	@echo "$(GREEN)Starting event simulator...$(NC)"
	$(PYTHON) -m app.utils.event_simulator

run-streaming: ## Run streaming job locally
	@echo "$(GREEN)Starting streaming job...$(NC)"
	$(PYTHON) -m app.jobs.streaming.advanced_streaming

run-ml: ## Run ML batch job locally
	@echo "$(GREEN)Starting ML batch job...$(NC)"
	$(PYTHON) -m app.jobs.batch.ml_analytics

# Monitoring targets
logs-streaming: ## Show streaming job logs
	$(KUBECTL) logs -f deployment/spark-streaming-advanced

logs-kafka: ## Show Kafka logs
	$(KUBECTL) logs -f my-cluster-kafka-0

status: ## Show deployment status
	@echo "$(GREEN)Checking deployment status...$(NC)"
	@echo "\nPods:"
	$(KUBECTL) get pods
	@echo "\nServices:"
	$(KUBECTL) get services
	@echo "\nDeployments:"
	$(KUBECTL) get deployments

query-mongo: ## Query MongoDB
	@bash deploy/scripts/demo_mongodb.sh

# Development targets
setup-env: ## Set up local development environment
	@echo "$(GREEN)Setting up development environment...$(NC)"
	cp config/.env.example config/.env
	@echo "Please edit config/.env with your settings"

minikube-start: ## Start Minikube
	@echo "$(GREEN)Starting Minikube...$(NC)"
	$(MINIKUBE) start --cpus=4 --memory=8192

minikube-stop: ## Stop Minikube
	@echo "$(YELLOW)Stopping Minikube...$(NC)"
	$(MINIKUBE) stop

minikube-delete: ## Delete Minikube cluster
	@echo "$(YELLOW)Deleting Minikube cluster...$(NC)"
	$(MINIKUBE) delete

port-forward-spark: ## Port forward Spark UI
	@echo "$(GREEN)Port forwarding Spark UI to localhost:4040$(NC)"
	$(KUBECTL) port-forward deployment/spark-streaming-advanced 4040:4040

port-forward-mongo: ## Port forward MongoDB
	@echo "$(GREEN)Port forwarding MongoDB to localhost:27017$(NC)"
	$(KUBECTL) port-forward svc/my-mongo-mongodb 27017:27017
