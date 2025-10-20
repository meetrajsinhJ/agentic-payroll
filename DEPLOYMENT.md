# Kubernetes Deployment Guide

Complete guide for deploying the Agentic AI Payroll System to Kubernetes.

## Prerequisites

✅ **Completed:**
- Docker installed (version 28.2.2)
- kubectl installed (v1.32.2)
- Minikube installed (v1.37.0)
- Minikube cluster running

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│           Kubernetes Cluster (Minikube)             │
│                                                       │
│  ┌──────────────────────────────────────────────┐  │
│  │  Namespace: payroll-system                    │  │
│  │                                                │  │
│  │  ┌─────────────────────────────────────────┐ │  │
│  │  │  CronJob: payroll-processor             │ │  │
│  │  │  Schedule: Monthly (1st @ 9AM)          │ │  │
│  │  │  or Manual Job                           │ │  │
│  │  └─────────────────────────────────────────┘ │  │
│  │                 ↓                              │  │
│  │  ┌─────────────────────────────────────────┐ │  │
│  │  │  Pod: agentic-payroll                   │ │  │
│  │  │  - Agent 1: Parser                      │ │  │
│  │  │  - Agent 2: Calculator                  │ │  │
│  │  │  - Agent 3: PDF Generator               │ │  │
│  │  └─────────────────────────────────────────┘ │  │
│  │                 ↓                              │  │
│  │  ┌─────────────────────────────────────────┐ │  │
│  │  │  PersistentVolume (5Gi)                 │ │  │
│  │  │  - /timesheets (input)                  │ │  │
│  │  │  - /salary_slips (output)               │ │  │
│  │  │  - /logs                                 │ │  │
│  │  └─────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Build Docker Image

```bash
# Build the Docker image for Minikube
eval $(minikube docker-env)
docker build -t agentic-payroll:latest .
```

### 2. Deploy to Kubernetes

```bash
# Apply all manifests in order
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-persistent-volume.yaml

# Wait for PVC to be bound
kubectl get pvc -n payroll-system --watch

# Deploy CronJob (for scheduled processing)
kubectl apply -f k8s/04-cronjob.yaml

# OR deploy one-time Job (for manual/testing)
kubectl apply -f k8s/05-job-manual.yaml
```

### 3. Upload Timesheets

```bash
# Copy timesheets to Minikube
minikube ssh
sudo mkdir -p /mnt/data/payroll/timesheets/excel
sudo cp /path/to/timesheets/* /mnt/data/payroll/timesheets/excel/
exit
```

### 4. Monitor Job Execution

```bash
# Watch job status
kubectl get jobs -n payroll-system --watch

# View logs
kubectl logs -n payroll-system -l app=agentic-payroll -f

# Get pod details
kubectl get pods -n payroll-system
kubectl describe pod <pod-name> -n payroll-system
```

### 5. Retrieve Salary Slips

```bash
# Access Minikube and copy output
minikube ssh
ls /mnt/data/payroll/salary_slips/
exit

# Copy files to local machine
kubectl cp payroll-system/<pod-name>:/app/salary_slips ./salary_slips
```

## Kubernetes Resources

### Namespace
- **Name:** `payroll-system`
- **Purpose:** Isolate payroll resources

### ConfigMap
- **Name:** `payroll-config`
- **Contains:** Environment variables (LOG_LEVEL, company info)

### PersistentVolume & PersistentVolumeClaim
- **Size:** 5Gi
- **Access Mode:** ReadWriteOnce
- **Storage Path:** `/mnt/data/payroll`

### CronJob
- **Name:** `payroll-processor`
- **Schedule:** `0 9 1 * *` (9 AM on 1st of each month)
- **For Testing:** Change to `*/5 * * * *` (every 5 minutes)

### Job (Manual)
- **Name:** `payroll-processor-manual`
- **Purpose:** One-time manual execution

## Resource Limits

```yaml
Resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Useful Commands

### Cluster Management
```bash
# Start Minikube
minikube start

# Stop Minikube
minikube stop

# Delete cluster
minikube delete

# Access Minikube dashboard
minikube dashboard
```

### Deployment Commands
```bash
# Apply all manifests
kubectl apply -f k8s/

# Delete all resources
kubectl delete -f k8s/

# Restart deployment
kubectl rollout restart cronjob/payroll-processor -n payroll-system
```

### Debugging Commands
```bash
# Get all resources in namespace
kubectl get all -n payroll-system

# Describe resources
kubectl describe cronjob payroll-processor -n payroll-system
kubectl describe pvc payroll-data-pvc -n payroll-system

# View logs
kubectl logs -n payroll-system <pod-name>
kubectl logs -n payroll-system <pod-name> --previous  # Previous run

# Execute commands in pod
kubectl exec -it <pod-name> -n payroll-system -- /bin/bash

# Port forwarding (if adding web UI later)
kubectl port-forward -n payroll-system <pod-name> 8000:8000
```

### Monitoring Commands
```bash
# Watch resources
kubectl get pods -n payroll-system --watch
kubectl get jobs -n payroll-system --watch

# Get events
kubectl get events -n payroll-system --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n payroll-system
kubectl top nodes
```

## Manual Job Execution

To run the job manually instead of waiting for the cron schedule:

```bash
# Create a manual job from the cronjob
kubectl create job --from=cronjob/payroll-processor manual-run-$(date +%s) -n payroll-system

# OR use the manual job manifest
kubectl apply -f k8s/05-job-manual.yaml

# Monitor the job
kubectl get jobs -n payroll-system
kubectl logs -n payroll-system job/payroll-processor-manual
```

## Testing the Deployment

```bash
# 1. Build image
eval $(minikube docker-env)
docker build -t agentic-payroll:latest .

# 2. Deploy
kubectl apply -f k8s/

# 3. Upload test timesheets
minikube cp timesheets/excel/ /mnt/data/payroll/timesheets/

# 4. Run manual job
kubectl apply -f k8s/05-job-manual.yaml

# 5. Check logs
kubectl logs -n payroll-system -l app=agentic-payroll -f

# 6. Verify output
minikube ssh
ls -la /mnt/data/payroll/salary_slips/
```

## Troubleshooting

### Pod not starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n payroll-system

# Common issues:
# - ImagePullBackOff: Image not built in Minikube's Docker
#   Solution: eval $(minikube docker-env) && docker build -t agentic-payroll:latest .
# - PVC not bound: Check PV status
#   Solution: kubectl get pv,pvc -n payroll-system
```

### Job fails
```bash
# Check job logs
kubectl logs -n payroll-system job/payroll-processor-manual

# Check for file access issues
minikube ssh
ls -la /mnt/data/payroll/
```

### No output files
```bash
# Verify input files exist
minikube ssh
ls /mnt/data/payroll/timesheets/excel/

# Check pod logs for errors
kubectl logs -n payroll-system <pod-name>
```

## CI/CD Pipeline (Next Steps)

See `.github/workflows/deploy.yml` for automated deployment pipeline.

### Pipeline Stages:
1. **Build:** Docker image creation
2. **Test:** Unit and integration tests
3. **Push:** Image to registry (Docker Hub/GitHub Container Registry)
4. **Deploy:** Update Kubernetes deployment
5. **Verify:** Health checks and smoke tests

## Production Considerations

### For Production Deployment:

1. **Use a real Kubernetes cluster** (EKS, GKE, AKS)
2. **Set up proper storage** (EBS, Persistent Disks, Azure Disks)
3. **Implement monitoring** (Prometheus, Grafana)
4. **Add logging** (ELK Stack, Loki)
5. **Set up alerts** (AlertManager, PagerDuty)
6. **Implement backups** for salary slip PDFs
7. **Add authentication** and authorization
8. **Use secrets management** (Kubernetes Secrets, HashiCorp Vault)
9. **Implement rate limiting** and resource quotas
10. **Set up disaster recovery** procedures

## Security Best Practices

1. Use read-only root filesystem
2. Run as non-root user
3. Implement network policies
4. Use Pod Security Standards
5. Scan images for vulnerabilities
6. Rotate secrets regularly
7. Implement RBAC
8. Enable audit logging

## Next Steps

- [ ] Set up CI/CD pipeline with GitHub Actions
- [ ] Add monitoring and alerting
- [ ] Implement backup strategy
- [ ] Add web UI for file upload
- [ ] Set up email notifications
- [ ] Deploy to cloud Kubernetes (EKS/GKE/AKS)
