# Kubernetes Deployments

This directory contains Kubernetes manifests for deploying the application.

## Structure

```
kubernetes/
├── base/                    # Base configurations
│   ├── kafka-strimzi.yaml  # Kafka cluster (Strimzi operator)
│   └── spark-deployments.yaml  # Spark streaming applications
├── overlays/
│   ├── dev/                # Development environment overrides
│   └── prod/               # Production environment overrides
```

## Deployment

### Using kubectl

```bash
# Deploy Kafka
kubectl apply -f base/kafka-strimzi.yaml

# Deploy Spark applications
kubectl apply -f base/spark-deployments.yaml
```

### Using Kustomize (for overlays)

```bash
# Development
kubectl apply -k overlays/dev/

# Production
kubectl apply -k overlays/prod/
```

## Components

- **Kafka (Strimzi)**: Message broker for event streaming
- **Spark Streaming**: Real-time analytics applications
- **MongoDB (Bitnami)**: Document database for analytics results
