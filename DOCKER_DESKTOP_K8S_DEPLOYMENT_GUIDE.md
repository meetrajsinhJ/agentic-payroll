# Docker Desktop Kubernetes Deployment Guide

**Date:** October 20, 2025
**System:** macOS with Docker Desktop
**Final Status:** ✅ SUCCESSFUL DEPLOYMENT

## Executive Summary

This document details the complete journey of deploying the Agentic AI Payroll System to Docker Desktop Kubernetes after Minikube failed due to volume mounting issues. The deployment was successful, processing 10 employee timesheets and generating salary slips with a total payroll of **$50,876.58**.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Problems Encountered & Solutions](#problems-encountered--solutions)
4. [Final Working Configuration](#final-working-configuration)
5. [Deployment Steps](#deployment-steps)
6. [Verification & Testing](#verification--testing)
7. [Lessons Learned](#lessons-learned)
8. [Next Steps](#next-steps)

---

## Prerequisites

### Installed Software
- ✅ Docker Desktop (with Kubernetes enabled)
- ✅ kubectl v1.32.2+
- ✅ Python 3.9
- ✅ Git (for version control)

### Kubernetes Context
```bash
kubectl config get-contexts
# Should show: docker-desktop (with kind cluster)
```

---

## Initial Setup

### 1. Enable Docker Desktop Kubernetes

**Steps:**
1. Open Docker Desktop
2. Go to Settings → Kubernetes
3. Select **kind** as cluster provisioning method
4. Check "Enable Kubernetes"
5. Click "Apply & Restart"
6. Wait 2-3 minutes for cluster to start

**Verification:**
```bash
kubectl config use-context docker-desktop
kubectl get nodes
```

**Expected Output:**
```
NAME                    STATUS   ROLES           AGE   VERSION
desktop-control-plane   Ready    control-plane   1h    v1.31.1
desktop-worker          Ready    <none>          1h    v1.31.1
```

### 2. Build Docker Image

```bash
# Build the image
docker build -t agentic-payroll:latest .

# Verify local image
docker images | grep agentic-payroll
```

**Output:**
```
agentic-payroll    latest    5b02bd45d082    12 minutes ago    697MB
```

---

## Problems Encountered & Solutions

### Problem 1: Image Not Available in Kubernetes Cluster

**Issue:**
After building the Docker image locally, Kubernetes pods showed:
```
Status: ErrImageNeverPull
```

**Root Cause:**
Docker Desktop Kubernetes uses **kind** (Kubernetes in Docker) internally. The image built in Docker Desktop's daemon is not automatically available to the kind cluster's containerd runtime.

**Error Logs:**
```bash
kubectl describe pod payroll-test-no-volumes-xxxxx -n payroll-system
```
```
Events:
  Type     Reason             Age    From               Message
  ----     ------             ----   ----               -------
  Normal   Scheduled          30s    default-scheduler  Successfully assigned...
  Warning  ErrImageNeverPull  28s    kubelet            Container image not present
```

**Solution 1 (Failed): Direct Copy**
```bash
# Tried to copy tar file to worker node
docker save agentic-payroll:latest -o /tmp/agentic-payroll.tar
docker cp /tmp/agentic-payroll.tar desktop-worker:/tmp/
docker exec desktop-worker ctr -n k8s.io images import /tmp/agentic-payroll.tar
# Error: file not found (permission/path issues)
```

**Solution 2 (SUCCESS): Stream via Pipe**
```bash
# Stream image directly into worker node's containerd
docker save agentic-payroll:latest | docker exec -i desktop-worker ctr -n k8s.io images import -

# Verify image is loaded
docker exec desktop-worker crictl images | grep agentic
```

**Output:**
```
docker.io/library/agentic-payroll    latest    5b02bd45d0824    720MB
unpacking docker.io/library/agentic-payroll:latest (sha256:72815308284b...)...done
```

**Key Learning:** Always load images into kind/containerd using pipe method for reliability.

---

### Problem 2: Volume Mounting Timeout with Multiple SubPaths

**Issue:**
Pods stuck at "ContainerCreating" indefinitely when mounting the same PVC with 3 different subPaths.

**Original Configuration (FAILED):**
```yaml
volumeMounts:
- name: timesheet-data
  mountPath: /app/timesheets
  subPath: timesheets
- name: salary-slip-data
  mountPath: /app/salary_slips
  subPath: salary_slips
- name: logs
  mountPath: /app/logs
  subPath: logs

volumes:
- name: timesheet-data
  persistentVolumeClaim:
    claimName: payroll-data-pvc
- name: salary-slip-data
  persistentVolumeClaim:
    claimName: payroll-data-pvc
- name: logs
  persistentVolumeClaim:
    claimName: payroll-data-pvc
```

**Error in Kubelet Logs:**
```bash
docker exec desktop-worker journalctl -u kubelet -n 50 | grep error
```
```
E1020 14:17:09 pod_workers.go:1301 "Error syncing pod, skipping"
err="unmounted volumes=[salary-slip-data timesheet-data], unattached volumes=[],
failed to process volumes=[salary-slip-data timesheet-data]: context deadline exceeded"
```

**Root Cause:**
Mounting the **same PVC three times with different subPaths** causes the kubelet volume manager to timeout after 2 minutes. This is a known limitation with hostPath volumes and multiple simultaneous mounts.

**Solution: Simplified Single Mount**
```yaml
volumeMounts:
- name: data
  mountPath: /data

volumes:
- name: data
  persistentVolumeClaim:
    claimName: payroll-data-pvc
```

**Key Changes Required in Application Code:**

1. **Update `main.py`:**
```python
def process_all_timesheets(timesheet_dir: str = None):
    # Auto-detect path: /data/timesheets/excel/ in K8s, ./timesheets/excel locally
    if timesheet_dir is None:
        if os.path.exists("/data/timesheets/excel"):
            timesheet_dir = "/data/timesheets/excel"
        else:
            timesheet_dir = "timesheets/excel"
```

2. **Update `agents/agent3_pdf_generator.py`:**
```python
def __init__(self, output_dir: str = None):
    self.name = "Salary Slip Generator Agent"
    # Auto-detect path: /data/salary_slips/ in K8s, ./salary_slips locally
    if output_dir is None:
        if os.path.exists("/data"):
            output_dir = "/data/salary_slips"
        else:
            output_dir = "salary_slips"
    self.output_dir = output_dir
```

**Result:** ✅ Pod started successfully in 9 seconds!

---

### Problem 3: ImagePullPolicy Configuration

**Issue:**
Initially used `imagePullPolicy: IfNotPresent`, but this still attempted to pull from remote registry.

**Original Setting:**
```yaml
image: agentic-payroll:latest
imagePullPolicy: IfNotPresent
```

**Updated Setting (After Loading Image):**
```yaml
image: agentic-payroll:latest
imagePullPolicy: IfNotPresent  # Works after image is loaded to containerd
```

**Note:** `imagePullPolicy: Never` can be used to strictly enforce local-only images, but `IfNotPresent` works fine once the image is loaded into containerd.

---

### Problem 4: File Copying to PersistentVolume

**Issue:**
Direct `kubectl cp` to PVC doesn't work - need to copy via a running pod.

**Solution: Use Helper Pod**
```bash
# Step 1: Create helper pod with volume mounted
kubectl apply -f - << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: file-copier
  namespace: payroll-system
spec:
  containers:
  - name: copier
    image: busybox
    command: ["sleep", "3600"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: payroll-data-pvc
EOF

# Step 2: Wait for pod to be ready
kubectl wait --for=condition=ready pod/file-copier -n payroll-system --timeout=60s

# Step 3: Create directory structure
kubectl exec -n payroll-system file-copier -- mkdir -p /data/timesheets/excel

# Step 4: Copy files
kubectl cp timesheets/excel file-copier:/data/timesheets/ -n payroll-system

# Step 5: Verify
kubectl exec -n payroll-system file-copier -- ls -la /data/timesheets/excel/

# Step 6: Clean up
kubectl delete pod file-copier -n payroll-system
```

---

## Final Working Configuration

### Directory Structure
```
agentic/
├── Dockerfile
├── main.py (updated with path detection)
├── agents/
│   ├── agent1_parser.py
│   ├── agent2_calculator.py
│   └── agent3_pdf_generator.py (updated with path detection)
├── k8s/
│   ├── 01-namespace.yaml
│   ├── 02-configmap.yaml
│   ├── 03-persistent-volume.yaml
│   └── 05-job-manual.yaml (updated with single volume mount)
├── timesheets/excel/
└── requirements.txt
```

### Kubernetes Manifests

**k8s/01-namespace.yaml**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: payroll-system
  labels:
    name: payroll-system
```

**k8s/02-configmap.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: payroll-config
  namespace: payroll-system
data:
  LOG_LEVEL: "INFO"
  PYTHONUNBUFFERED: "1"
  COMPANY_NAME: "Tech Solutions Inc."
  COMPANY_ADDRESS: "123 Business Ave, Suite 100"
```

**k8s/03-persistent-volume.yaml**
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: payroll-data-pv
  labels:
    type: local
spec:
  storageClassName: manual
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/mnt/data/payroll"
    type: DirectoryOrCreate
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: payroll-data-pvc
  namespace: payroll-system
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

**k8s/05-job-manual.yaml**
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: payroll-processor-manual
  namespace: payroll-system
  labels:
    app: agentic-payroll
    component: batch-processor
    run-type: manual
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 3600

  template:
    metadata:
      labels:
        app: agentic-payroll
        component: batch-processor
        run-type: manual
    spec:
      restartPolicy: OnFailure

      containers:
      - name: payroll-processor
        image: agentic-payroll:latest
        imagePullPolicy: IfNotPresent

        envFrom:
        - configMapRef:
            name: payroll-config

        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

        volumeMounts:
        - name: data
          mountPath: /data

      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: payroll-data-pvc
```

---

## Deployment Steps

### Complete Step-by-Step Process

#### Step 1: Verify Prerequisites
```bash
# Check Docker Desktop Kubernetes is running
kubectl get nodes

# Expected output: 2 nodes (control-plane + worker) in Ready state
```

#### Step 2: Build and Load Docker Image
```bash
# Build the image
docker build -t agentic-payroll:latest .

# Load into kind cluster
docker save agentic-payroll:latest | docker exec -i desktop-worker ctr -n k8s.io images import -

# Verify
docker exec desktop-worker crictl images | grep agentic
```

#### Step 3: Deploy Kubernetes Resources
```bash
# Create namespace
kubectl apply -f k8s/01-namespace.yaml

# Create ConfigMap
kubectl apply -f k8s/02-configmap.yaml

# Create PersistentVolume and PVC
kubectl apply -f k8s/03-persistent-volume.yaml

# Verify PVC is bound
kubectl get pvc -n payroll-system
# Expected: STATUS = Bound
```

#### Step 4: Upload Timesheet Files
```bash
# Create helper pod
kubectl apply -f - << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: file-copier
  namespace: payroll-system
spec:
  containers:
  - name: copier
    image: busybox
    command: ["sleep", "3600"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: payroll-data-pvc
EOF

# Wait for pod
kubectl wait --for=condition=ready pod/file-copier -n payroll-system --timeout=60s

# Create directory
kubectl exec -n payroll-system file-copier -- mkdir -p /data/timesheets/excel

# Copy files
kubectl cp timesheets/excel file-copier:/data/timesheets/ -n payroll-system

# Verify
kubectl exec -n payroll-system file-copier -- ls -la /data/timesheets/excel/

# Delete helper pod
kubectl delete pod file-copier -n payroll-system
```

#### Step 5: Run the Payroll Processing Job
```bash
# Deploy the job
kubectl apply -f k8s/05-job-manual.yaml

# Watch the pod
kubectl get pods -n payroll-system --watch

# Expected: Status changes from ContainerCreating → Running → Completed (in ~9 seconds)
```

#### Step 6: View Logs
```bash
# View complete logs
kubectl logs -n payroll-system -l app=agentic-payroll

# Expected output shows:
# - 10 timesheets processed
# - All salary slips generated
# - Total payroll: $50,876.58
```

#### Step 7: Extract Salary Slips
```bash
# Create helper pod to access volume
kubectl apply -f - << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: file-checker
  namespace: payroll-system
spec:
  containers:
  - name: checker
    image: busybox
    command: ["sleep", "300"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: payroll-data-pvc
EOF

# Wait for pod
kubectl wait --for=condition=ready pod/file-checker -n payroll-system --timeout=30s

# Verify files exist
kubectl exec -n payroll-system file-checker -- ls -la /data/salary_slips/

# Copy to local machine
kubectl cp payroll-system/file-checker:/data/salary_slips ./output_salary_slips

# Verify locally
ls -la output_salary_slips/

# Clean up
kubectl delete pod file-checker -n payroll-system
```

---

## Verification & Testing

### Test 1: Job Without Volumes (Diagnostic Test)

**Purpose:** Verify that the container and image work correctly before adding volume complexity.

```bash
kubectl apply -f - << 'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: payroll-test-no-volumes
  namespace: payroll-system
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: test
        image: agentic-payroll:latest
        imagePullPolicy: IfNotPresent
        command: ["python", "-c", "print('SUCCESS!'); import sys; sys.exit(0)"]
EOF

kubectl get pods -n payroll-system --watch
```

**Expected Result:** Pod completes successfully in <30 seconds.

**If Failed:** Issue is with image loading, not volumes.

### Test 2: Job With Volumes (Full Test)

```bash
kubectl apply -f k8s/05-job-manual.yaml
kubectl get pods -n payroll-system --watch
```

**Expected Result:** Pod completes in ~9 seconds.

**Success Indicators:**
- Pod status: Completed
- Exit code: 0
- Logs show "✓ SALARY SLIPS GENERATED SUCCESSFULLY!"
- 10 PDF files in `/data/salary_slips/`

### Final Verification

**Check Files in Volume:**
```bash
kubectl exec -n payroll-system file-checker -- ls -laR /data/
```

**Expected Output:**
```
/data/salary_slips:
total 88
-rw-r--r--    1 root     root          4133 Oct 20 14:32 EMP001_John_Smith_SalarySlip_20251031.pdf
-rw-r--r--    1 root     root          4138 Oct 20 14:32 EMP002_Sarah_Johnson_SalarySlip_20251031.pdf
-rw-r--r--    1 root     root          4122 Oct 20 14:32 EMP003_Michael_Chen_SalarySlip_20251031.pdf
-rw-r--r--    1 root     root          4128 Oct 20 14:32 EMP004_Emily_Davis_SalarySlip_20251031.pdf
-rw-r--r--    1 root     root          4133 Oct 20 14:32 EMP005_David_Martinez_SalarySlip_20251031.pdf
-rw-r--r--    1 root     root          4127 Oct 20 14:32 EMP006_Jessica_Taylor_SalarySlip_20251031.pdf
-rw-r--r--    1 root     root          4132 Oct 20 14:32 EMP007_Robert_Anderson_SalarySlip_20251031.pdf
-rw-r--r--    1 root     root          4126 Oct 20 14:32 EMP008_Lisa_Wong_SalarySlip_20251031.pdf
-rw-r--r--    1 root     root          4133 Oct 20 14:32 EMP009_James_Brown_SalarySlip_20251031.pdf
-rw-r--r--    1 root     root          4119 Oct 20 14:32 EMP010_Maria_Garcia_SalarySlip_20251031.pdf
```

**Processing Summary from Logs:**
```
Total Timesheets Processed: 10
✓ Successful: 10
✗ Failed: 0
💰 Total Payroll: $50,876.58
```

---

## Lessons Learned

### 1. Kind Cluster Image Loading

**Problem:** Images built locally aren't automatically available to kind clusters.

**Solution:** Always load images explicitly:
```bash
docker save <image> | docker exec -i <worker-node> ctr -n k8s.io images import -
```

**Best Practice:** Create a helper script for rebuilding and loading:
```bash
#!/bin/bash
docker build -t agentic-payroll:latest .
docker save agentic-payroll:latest | docker exec -i desktop-worker ctr -n k8s.io images import -
echo "✅ Image loaded successfully"
```

### 2. Volume Mounting Complexity

**Problem:** Multiple subPath mounts of the same PVC cause timeouts.

**Solution:** Use single mount point and structure directories appropriately.

**Design Pattern:**
```
Mount /data → PVC
Application uses:
  - /data/timesheets/excel/ (input)
  - /data/salary_slips/ (output)
  - /data/logs/ (logs)
```

**Code Pattern:** Auto-detect environment
```python
def get_path(local_path, k8s_path):
    return k8s_path if os.path.exists(k8s_path) else local_path
```

### 3. File Transfer to PVCs

**Problem:** Cannot directly `kubectl cp` to PVCs.

**Solution:** Use temporary pods as intermediaries.

**Pattern:**
1. Create pod with PVC mounted
2. Wait for pod to be ready
3. `kubectl cp` to pod
4. Verify files
5. Delete temporary pod

### 4. Debugging Workflow

**Effective Debugging Order:**
1. Test container without volumes first
2. Check image is loaded: `crictl images`
3. Check kubelet logs: `journalctl -u kubelet`
4. Simplify volume configuration
5. Test with minimal setup

### 5. Path Handling Best Practices

**Always make code environment-agnostic:**
- Use environment variables or path detection
- Don't hardcode absolute paths
- Support both local and containerized execution

### 6. Resource Cleanup

**Always clean up test resources:**
```bash
kubectl delete job <job-name> -n payroll-system
kubectl delete pod <pod-name> -n payroll-system
```

**Check what's running:**
```bash
kubectl get all -n payroll-system
```

---

## Troubleshooting Guide

### Issue: Pod Stuck at "ContainerCreating"

**Check 1: Is image loaded?**
```bash
docker exec desktop-worker crictl images | grep agentic
```

**Check 2: What's the error?**
```bash
kubectl describe pod <pod-name> -n payroll-system
```

**Check 3: Volume mounting issues?**
```bash
docker exec desktop-worker journalctl -u kubelet -n 50 | grep -i error
```

**Solutions:**
- Image missing: Load with `docker save | docker exec -i`
- Volume timeout: Simplify to single mount
- Permission issues: Check hostPath permissions

### Issue: Job Fails Immediately

**Check logs:**
```bash
kubectl logs -n payroll-system -l app=agentic-payroll
```

**Common Causes:**
- Missing input files
- Path configuration incorrect
- Python dependencies missing

**Solution:**
- Verify files in volume
- Check path detection logic
- Rebuild image with dependencies

### Issue: Files Not in Volume After Job Completes

**Check 1: Where did files go?**
```bash
kubectl logs -n payroll-system <pod-name> | grep "generated"
```

**Check 2: Is path correct?**
```bash
kubectl exec -n payroll-system file-checker -- find /data -name "*.pdf"
```

**Solution:**
- Update code to use correct paths
- Rebuild and reload image
- Rerun job

### Issue: Cannot Access Volume

**Check PVC status:**
```bash
kubectl get pvc -n payroll-system
```

**Check PV status:**
```bash
kubectl get pv
```

**Expected:** Both should show "Bound"

**If Pending:**
- Check StorageClass exists
- Verify hostPath is accessible
- Check PV/PVC spec matches

---

## Performance Metrics

### Successful Deployment Stats

- **Total Employees Processed:** 10
- **Success Rate:** 100% (10/10)
- **Processing Time:** ~9 seconds
- **Total Payroll Calculated:** $50,876.58
- **Files Generated:** 10 PDF salary slips
- **Average Processing Time per Employee:** <1 second
- **Container Image Size:** 697MB
- **Resource Usage:**
  - CPU Request: 500m
  - Memory Request: 512Mi
  - CPU Limit: 1 core
  - Memory Limit: 1Gi

### Individual Employee Results

| # | Employee | Net Salary | Status | PDF Size |
|---|----------|-----------|--------|----------|
| 1 | David Martinez | $5,373.43 | ✅ | 4.1 KB |
| 2 | Michael Chen | $5,958.15 | ✅ | 4.1 KB |
| 3 | Sarah Johnson | $5,991.73 | ✅ | 4.1 KB |
| 4 | Jessica Taylor | $5,286.64 | ✅ | 4.1 KB |
| 5 | Maria Garcia | $4,818.48 | ✅ | 4.1 KB |
| 6 | Lisa Wong | $5,697.15 | ✅ | 4.1 KB |
| 7 | Emily Davis | $3,940.45 | ✅ | 4.1 KB |
| 8 | James Brown | $4,279.38 | ✅ | 4.1 KB |
| 9 | Robert Anderson | $4,133.67 | ✅ | 4.1 KB |
| 10 | John Smith | $5,397.50 | ✅ | 4.1 KB |

---

## Comparison: Minikube vs Docker Desktop Kubernetes

| Aspect | Minikube | Docker Desktop K8s | Winner |
|--------|----------|-------------------|--------|
| **Setup Complexity** | Medium (separate install) | Easy (built-in) | Docker Desktop |
| **Volume Mounting** | ❌ Failed (timeout) | ✅ Works perfectly | Docker Desktop |
| **Image Loading** | Need `eval $(minikube docker-env)` | Need explicit import | Tie |
| **macOS Integration** | Poor (VM-based) | Excellent (native) | Docker Desktop |
| **Resource Usage** | Higher (VM overhead) | Lower (container-based) | Docker Desktop |
| **File Copying** | Complex (`minikube cp`) | Standard (`kubectl cp`) | Docker Desktop |
| **Troubleshooting** | Multiple layers (VM + K8s) | Simpler (just K8s) | Docker Desktop |
| **Production-like** | More similar to cloud | Less similar to cloud | Minikube |

**Recommendation for Local Development on macOS:** Docker Desktop Kubernetes

---

## Next Steps

### Immediate Next Steps

1. **✅ Test CI/CD Pipeline**
   - Set up GitHub Actions
   - Automate build and deployment
   - Add automated testing

2. **Schedule Automatic Processing**
   - Deploy CronJob for monthly processing
   - Set up monitoring
   - Configure email notifications

3. **Add Observability**
   - Prometheus metrics
   - Grafana dashboards
   - Log aggregation (ELK stack)

### Future Enhancements

1. **Web UI**
   - File upload interface
   - Real-time processing status
   - Download salary slips

2. **Database Integration**
   - PostgreSQL for employee data
   - Historical salary records
   - Audit logging

3. **Cloud Deployment**
   - AWS EKS
   - Google GKE
   - Azure AKS

4. **Security Enhancements**
   - RBAC configuration
   - Secret management (Vault)
   - Network policies
   - Pod security policies

5. **Scalability**
   - Horizontal pod autoscaling
   - Batch processing for large datasets
   - Queue-based architecture (Redis/RabbitMQ)

---

## Useful Commands Reference

### Image Management
```bash
# Build image
docker build -t agentic-payroll:latest .

# Load into kind cluster
docker save agentic-payroll:latest | docker exec -i desktop-worker ctr -n k8s.io images import -

# List images in cluster
docker exec desktop-worker crictl images
```

### Resource Management
```bash
# Apply all manifests
kubectl apply -f k8s/

# Get all resources
kubectl get all -n payroll-system

# Delete all resources
kubectl delete -f k8s/
```

### Job Management
```bash
# Run manual job
kubectl apply -f k8s/05-job-manual.yaml

# Watch job
kubectl get jobs -n payroll-system --watch

# View logs
kubectl logs -n payroll-system -l app=agentic-payroll

# Delete job
kubectl delete job payroll-processor-manual -n payroll-system
```

### Volume Operations
```bash
# Check PVC status
kubectl get pvc -n payroll-system

# Check PV status
kubectl get pv

# Access volume via helper pod
kubectl exec -n payroll-system file-checker -- ls /data/
```

### Debugging
```bash
# Describe pod
kubectl describe pod <pod-name> -n payroll-system

# View events
kubectl get events -n payroll-system --sort-by='.lastTimestamp'

# Check kubelet logs
docker exec desktop-worker journalctl -u kubelet -n 50

# Get pod logs
kubectl logs <pod-name> -n payroll-system --previous
```

### File Operations
```bash
# Copy files to pod
kubectl cp <local-path> <namespace>/<pod-name>:<remote-path>

# Copy files from pod
kubectl cp <namespace>/<pod-name>:<remote-path> <local-path>
```

---

## Conclusion

After extensive troubleshooting with Minikube (documented in `MINIKUBE_TROUBLESHOOTING.md`), we successfully deployed the Agentic AI Payroll System to Docker Desktop Kubernetes.

**Key Success Factors:**
1. Simplified volume mounting configuration (single mount instead of multiple subPaths)
2. Proper image loading into kind cluster using pipe method
3. Environment-agnostic path detection in application code
4. Systematic debugging approach starting with minimal configuration

**Final Result:**
- ✅ 100% success rate (10/10 employees processed)
- ✅ Total payroll: $50,876.58
- ✅ All salary slips generated and extracted
- ✅ Processing time: ~9 seconds
- ✅ Ready for CI/CD automation

**Recommendation:** For local Kubernetes development on macOS, Docker Desktop Kubernetes with kind is significantly more reliable than Minikube, especially for workloads requiring PersistentVolumes.

---

## Appendix: Error Log Summary

### Errors Encountered (In Chronological Order)

1. ❌ **ErrImageNeverPull** - Image not available in kind cluster
   - **Solution:** Load image with `docker save | docker exec -i ctr import`

2. ❌ **Volume mounting timeout** - Multiple subPath mounts
   - **Solution:** Use single mount point at `/data`

3. ❌ **Path not found** - Hardcoded local paths in code
   - **Solution:** Auto-detect paths based on environment

4. ❌ **File copy failed** - Direct `kubectl cp` to PVC
   - **Solution:** Use helper pods for file transfer

5. ✅ **All issues resolved** - Successful deployment

### Time Investment

- **Total debugging time:** ~3 hours
- **Minikube attempts:** Multiple (documented separately)
- **Docker Desktop attempts:** 2
- **Final successful deployment:** First try after image loading fix

---

**Document Version:** 1.0
**Last Updated:** October 20, 2025
**Status:** Production-ready for local development
**Next Review:** Before cloud deployment
