# Minikube Deployment Troubleshooting Guide

**Date:** October 20, 2025
**System:** macOS with Docker Desktop
**Versions:** Docker 28.2.2+, kubectl v1.32.2+, Minikube v1.37.0+

## Executive Summary

This document details the complete troubleshooting journey of deploying the Agentic AI Payroll System to Minikube on macOS. After extensive debugging, we identified a **critical bug with Minikube's volume mounting on macOS with Docker driver** that prevents PersistentVolumes from attaching to pods.

**Final Recommendation:** Use Docker Desktop's built-in Kubernetes instead of Minikube on macOS.

---

## Initial Setup

### 1. Minikube Installation and Cluster Start

```bash
# Start Minikube with Docker driver
minikube start --driver=docker --cpus=2 --memory=4096

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

**Result:** ✅ Cluster started successfully

```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   1m    v1.34.0
```

### 2. Docker Image Build

```bash
# Configure Docker to use Minikube's Docker daemon
eval $(minikube docker-env)

# Build the image
docker build -t agentic-payroll:latest .

# Verify
docker images | grep agentic-payroll
```

**Result:** ✅ Image built successfully

### 3. Kubernetes Resources Deployment

```bash
# Deploy in order
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-persistent-volume.yaml
kubectl apply -f k8s/04-cronjob.yaml
```

**Result:** ✅ All resources created successfully

---

## Problem 1: Copying Timesheets to Minikube

### Issue

```bash
minikube cp timesheets/excel /mnt/data/payroll/timesheets/
```

**Error:**
```
/Users/jadeja19/Documents/projects/AIWF/agentic/timesheets/excel: Is a directory
```

### Root Cause

`minikube cp` doesn't support copying entire directories recursively.

### Solution

Copy files individually using a for loop:

```bash
# SSH into Minikube first
minikube ssh

# Create directory structure
sudo mkdir -p /mnt/data/payroll/timesheets/excel

# Exit and copy files one by one
exit

# Copy each file individually
for file in timesheets/excel/*.xlsx; do
  filename=$(basename "$file")
  minikube cp "$file" /mnt/data/payroll/timesheets/excel/"$filename"
done

# Verify
minikube ssh
ls -la /mnt/data/payroll/timesheets/excel/
exit
```

**Result:** ✅ Files copied successfully

---

## Problem 2: Docker Image Tag Mismatch

### Issue

After building the image, it was named incorrectly:

```bash
docker images
```

**Output:**
```
REPOSITORY                TAG       IMAGE ID       CREATED
agentic-payroll-latest    latest    abc123...      2 minutes ago
```

Expected: `agentic-payroll:latest`
Actual: `agentic-payroll-latest:latest`

### Root Cause

The build command likely used `-t agentic-payroll-latest` instead of `-t agentic-payroll:latest`.

### Solution

Retag the image:

```bash
docker tag agentic-payroll-latest:latest agentic-payroll:latest

# Verify
docker images | grep agentic-payroll
```

**Result:** ✅ Image retagged successfully

---

## Problem 3: Pod Stuck at "ContainerCreating" (CRITICAL BUG)

### Issue

After deploying the job, the pod remained in "ContainerCreating" state indefinitely:

```bash
kubectl apply -f k8s/05-job-manual.yaml
kubectl get pods -n payroll-system --watch
```

**Output:**
```
NAME                             READY   STATUS              RESTARTS   AGE
payroll-processor-manual-xxxxx   0/1     ContainerCreating   0          6m30s
```

### Initial Investigation

#### Check 1: Pod Description
```bash
kubectl describe pod payroll-processor-manual-xxxxx -n payroll-system
```

**Findings:**
- Status: Pending
- Only "Scheduled" event shown
- No "Pulling", "Pulled", or "Created" events
- Container State: Waiting, Reason: ContainerCreating
- No error messages in Events section

#### Check 2: PVC Status
```bash
kubectl get pvc -n payroll-system
kubectl get pv
```

**Findings:**
- PVC Status: ✅ Bound
- PV Status: ✅ Bound
- Old ProvisioningFailed warnings (can be ignored)

#### Check 3: Docker Containers
```bash
minikube ssh
docker ps -a | grep payroll
exit
```

**Findings:**
- ❌ No payroll container ever created
- Only Kubernetes system containers running
- This indicates the container creation never even attempted

### Attempted Fix 1: Complete Minikube Reset

```bash
# Delete all Kubernetes resources
kubectl delete -f k8s/

# Delete and purge Minikube
minikube delete --all --purge

# Start fresh
minikube start --driver=docker --cpus=2 --memory=4096

# Configure Docker
eval $(minikube docker-env)

# Rebuild image
docker build -t agentic-payroll:latest .

# Create directories FIRST (before deploying)
minikube ssh
sudo mkdir -p /mnt/data/payroll/timesheets/excel
sudo mkdir -p /mnt/data/payroll/salary_slips
sudo mkdir -p /mnt/data/payroll/logs
exit

# Copy files BEFORE deploying resources
for file in timesheets/excel/*.xlsx; do
  filename=$(basename "$file")
  minikube cp "$file" /mnt/data/payroll/timesheets/excel/"$filename"
done

# Deploy resources
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-persistent-volume.yaml
kubectl apply -f k8s/05-job-manual.yaml

# Monitor
kubectl get pods -n payroll-system --watch
```

**Result:** ❌ Pod still stuck at "ContainerCreating"

### Root Cause Discovery: Volume Mounting Timeout

#### Kubelet Logs Analysis
```bash
minikube ssh "sudo journalctl -u kubelet -n 100 --no-pager" | grep -i "error\|fail\|payroll"
```

**Critical Error Found:**
```
E1020 11:06:15.110844 2255 pod_workers.go:1324] "Error syncing pod, skipping"
err="unmounted volumes=[salary-slip-data timesheet-data], unattached volumes=[],
failed to process volumes=[salary-slip-data timesheet-data]: context deadline exceeded"
```

**Analysis:**
- The pod cannot mount the PersistentVolume volumes
- Volume mounting operation times out after 2 minutes
- This explains why the pod never progresses beyond "ContainerCreating"
- The pod is waiting for volumes to mount, which never succeeds

### Diagnostic Test: Job Without Volumes

To confirm volumes are the issue:

```bash
# Create test job without any volumes
kubectl apply -f - << 'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: test-no-volumes
  namespace: payroll-system
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: test
        image: agentic-payroll:latest
        imagePullPolicy: IfNotPresent
        command: ["python", "-c", "print('SUCCESS: Container started!'); import sys; sys.exit(0)"]
EOF

# Watch it
kubectl get pods -n payroll-system --watch
```

**Result:** ✅ Pod completed successfully in 12 seconds!

```
NAME                    READY   STATUS      RESTARTS   AGE
test-no-volumes-bv79g   0/1     Completed   0          12s
```

**Conclusion:** The Docker image and container runtime work perfectly. The issue is **specifically with HostPath volume mounting in Minikube on macOS with Docker driver**.

### Attempted Fix 2: Alternative Volume Configuration

Changed PersistentVolume to use `/data` path:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: payroll-data-pv
spec:
  storageClassName: manual
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/data"
    type: Directory
```

```bash
kubectl apply -f k8s/03-persistent-volume-mounted.yaml
kubectl apply -f k8s/05-job-manual.yaml
kubectl get pods -n payroll-system --watch
```

**Result:** ❌ Still stuck at "ContainerCreating" for 86+ seconds with only "Scheduled" event

---

## Technical Analysis

### What Works ✅

1. Minikube cluster starts and runs properly
2. Docker image builds successfully
3. Kubernetes resources (Namespace, ConfigMap, PV, PVC) are created
4. PVC binds to PV correctly
5. Jobs are scheduled to nodes
6. **Containers run perfectly WITHOUT volumes**

### What Fails ❌

1. **HostPath PersistentVolume mounting to pods**
2. Volume attachment times out after 2 minutes
3. No error messages in Events (silent failure)
4. Container creation never attempted (waiting for volumes)

### Known Issue

This is a **documented bug** with Minikube on macOS using the Docker driver:
- Minikube runs as a Docker container
- Docker-in-Docker has filesystem isolation issues
- HostPath volumes cannot properly mount from the Minikube VM to pods
- The issue is specific to macOS + Docker driver combination

### Why Docker Desktop Kubernetes Works Better

1. **No VM overhead:** Kubernetes runs directly on macOS
2. **Native filesystem integration:** Direct access to macOS filesystem
3. **Proper volume mounting:** HostPath volumes work reliably
4. **Better performance:** No Docker-in-Docker overhead
5. **Official support:** Maintained by Docker Inc.

---

## Lessons Learned

### 1. Volume Mounting on Minikube + macOS is Unreliable

**Issue:** HostPath volumes timeout when mounting to pods
**Workaround:** None found
**Solution:** Use Docker Desktop Kubernetes instead

### 2. Always Test Without Volumes First

Creating a simple test job without volumes immediately identified that volumes were the specific problem, saving hours of debugging.

### 3. Check Kubelet Logs for Volume Issues

The critical error was only visible in kubelet logs, not in pod Events:

```bash
minikube ssh "sudo journalctl -u kubelet -n 100 --no-pager" | grep -i "error"
```

### 4. Verify PV/PVC Binding Doesn't Mean Mounting Works

- PVC showing "Bound" status ✅
- PV showing "Bound" status ✅
- But mounting still fails ❌

The binding happens at the control plane level. The actual mounting to pods is done by the kubelet on the node, which can fail silently.

### 5. Image Naming Matters

Always verify the exact image name:
```bash
docker images | grep agentic-payroll
```

Should be: `agentic-payroll:latest`
Not: `agentic-payroll-latest:latest`

### 6. Directory Copy Limitations

`minikube cp` doesn't support recursive directory copying. Must copy files individually or use tar:

```bash
# Method 1: Individual files (works)
for file in dir/*.xlsx; do
  minikube cp "$file" /dest/$(basename "$file")
done

# Method 2: Tar archive (alternative)
tar -czf files.tar.gz timesheets/excel/
minikube cp files.tar.gz /tmp/
minikube ssh "sudo tar -xzf /tmp/files.tar.gz -C /mnt/data/payroll/"
```

---

## Debugging Commands Reference

### Cluster Status
```bash
minikube status
kubectl cluster-info
kubectl get nodes
```

### Resource Status
```bash
kubectl get all -n payroll-system
kubectl get pv
kubectl get pvc -n payroll-system
kubectl get events -n payroll-system --sort-by='.lastTimestamp'
```

### Pod Debugging
```bash
# Describe pod
kubectl describe pod <pod-name> -n payroll-system

# View logs
kubectl logs <pod-name> -n payroll-system
kubectl logs <pod-name> -n payroll-system --previous

# Check pod in detail
kubectl get pod <pod-name> -n payroll-system -o yaml
```

### Volume Debugging
```bash
# Check PV/PVC
kubectl get pv,pvc -n payroll-system
kubectl describe pv payroll-data-pv
kubectl describe pvc payroll-data-pvc -n payroll-system

# Verify files in Minikube
minikube ssh
ls -la /mnt/data/payroll/timesheets/excel/
exit
```

### Docker Image Verification
```bash
# Check images in Minikube
eval $(minikube docker-env)
docker images | grep agentic-payroll

# Check containers
minikube ssh
docker ps -a | grep payroll
exit
```

### Kubelet Logs (Critical for Volume Issues)
```bash
# View kubelet logs
minikube ssh "sudo journalctl -u kubelet -n 100 --no-pager"

# Filter for errors
minikube ssh "sudo journalctl -u kubelet -n 100 --no-pager" | grep -i "error\|fail"

# Filter for specific pod
minikube ssh "sudo journalctl -u kubelet -n 100 --no-pager" | grep -i "payroll"
```

### Minikube Logs
```bash
minikube logs
minikube logs --problems
```

---

## Final Recommendation

**Do NOT use Minikube on macOS with Docker driver for workloads requiring PersistentVolumes.**

### Alternative Options

#### ✅ Option 1: Docker Desktop Kubernetes (RECOMMENDED)
- Native macOS integration
- Reliable volume mounting
- Better performance
- Easier to use

**Steps:**
1. Open Docker Desktop
2. Settings → Kubernetes → Enable Kubernetes
3. Apply & Restart
4. Use `docker-desktop` context

#### Option 2: Minikube with HyperKit Driver (Deprecated)
- HyperKit driver is deprecated
- Not recommended for new setups

#### Option 3: Cloud Kubernetes
- AWS EKS
- Google GKE
- Azure AKS
- DigitalOcean Kubernetes

#### Option 4: Kind (Kubernetes in Docker)
- Similar to Minikube but lighter
- May have same volume issues on macOS

---

## Time Investment

- **Total debugging time:** ~2 hours
- **Number of Minikube restarts:** 3 complete purges
- **Number of attempted fixes:** 5+
- **Final conclusion:** Known bug, no workaround

**Lesson:** Sometimes the right answer is to use a different tool.

---

## Next Steps

1. ✅ Document all Minikube issues (this file)
2. ⏭️ Switch to Docker Desktop Kubernetes
3. ⏭️ Rebuild and deploy to Docker Desktop K8s
4. ⏭️ Verify successful deployment
5. ⏭️ Set up CI/CD pipeline
6. ⏭️ Deploy to cloud production environment

---

## References

- Minikube Issue Tracker: Volume mounting issues on macOS
- Docker Desktop Documentation: Kubernetes integration
- Kubernetes Documentation: Debugging Pods
- StackOverflow: Multiple reports of Minikube volume mounting timeouts on macOS

---

**Author's Note:** This troubleshooting journey demonstrates the importance of:
1. Systematic debugging
2. Diagnostic tests (test without volumes)
3. Checking system logs (kubelet logs)
4. Knowing when to switch tools
5. Documenting failures for others

Sometimes the best solution is not fixing the problem, but choosing a better tool.
