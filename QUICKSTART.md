# Quick Start Guide - Kubernetes Deployment

Get the Agentic AI Payroll System running on Kubernetes in under 10 minutes!

## ✅ Prerequisites Check

```bash
# Verify installations
docker --version        # Should show: Docker version 28.2.2+
kubectl version --client  # Should show: v1.32.2+
minikube version       # Should show: v1.37.0+
```

## 🚀 Step 1: Start Minikube (2 minutes)

```bash
minikube start --driver=docker --cpus=2 --memory=4096

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

**Expected Output:**
```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   1m    v1.34.0
```

## 🐳 Step 2: Build Docker Image (2 minutes)

```bash
# Configure Docker to use Minikube's Docker daemon
eval $(minikube docker-env)

# Build the image
docker build -t agentic-payroll:latest .

# Verify image was built
docker images | grep agentic-payroll
```

## ☸️ Step 3: Deploy to Kubernetes (1 minute)

```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-persistent-volume.yaml
kubectl apply -f k8s/04-cronjob.yaml

# Verify deployment
kubectl get all -n payroll-system
```

## 📁 Step 4: Upload Test Timesheets (1 minute)

```bash
# SSH into Minikube
minikube ssh

# Create directory and copy files
sudo mkdir -p /mnt/data/payroll/timesheets/excel
sudo cp -r /hosthome/$(whoami)/Documents/projects/AIWF/agentic/timesheets/excel/* \
  /mnt/data/payroll/timesheets/excel/

# Verify files
ls -la /mnt/data/payroll/timesheets/excel/
exit
```

## ▶️ Step 5: Run the Job Manually (3 minutes)

```bash
# Create a manual job
kubectl apply -f k8s/05-job-manual.yaml

# Watch the job
kubectl get jobs -n payroll-system --watch

# View logs in real-time
kubectl logs -n payroll-system -l app=agentic-payroll -f
```

## 📥 Step 6: Download Salary Slips (1 minute)

```bash
# Get the pod name
POD_NAME=$(kubectl get pods -n payroll-system -l app=agentic-payroll -o jsonpath='{.items[0].metadata.name}')

# Copy salary slips to local machine
kubectl cp payroll-system/$POD_NAME:/app/salary_slips ./output_salary_slips

# Verify files
ls -la output_salary_slips/
```

## 🎉 Success!

You should now see 10 salary slip PDFs in the `output_salary_slips/` directory!

---

## 🔄 Next Steps

### Option A: Schedule Automatic Processing

The CronJob is already configured to run on the 1st of every month at 9 AM.

To test the schedule immediately:

```bash
# Edit the cron schedule to run every 5 minutes
kubectl edit cronjob payroll-processor -n payroll-system

# Change the schedule line to:
# schedule: "*/5 * * * *"

# Watch for automatic executions
kubectl get jobs -n payroll-system --watch
```

### Option B: Set Up CI/CD Pipeline

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Agentic AI Payroll System"
   git remote add origin https://github.com/YOUR-USERNAME/agentic-payroll.git
   git push -u origin main
   ```

2. **Configure GitHub Secrets** (for production deployment):
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Add: `KUBE_CONFIG` (your Kubernetes config file, base64 encoded)

3. **Trigger the pipeline:**
   - Push any change to `main` branch
   - Or manually trigger from Actions tab

### Option C: Deploy to Cloud

See `DEPLOYMENT.md` for instructions on deploying to:
- AWS EKS
- Google GKE
- Azure AKS
- DigitalOcean Kubernetes

---

## 🐛 Troubleshooting

### Issue: Pod shows "ImagePullBackOff"

**Solution:**
```bash
# Rebuild image in Minikube's Docker
eval $(minikube docker-env)
docker build -t agentic-payroll:latest .
kubectl delete job payroll-processor-manual -n payroll-system
kubectl apply -f k8s/05-job-manual.yaml
```

### Issue: Job fails with "No such file or directory"

**Solution:**
```bash
# Verify timesheets are in the correct location
minikube ssh
ls /mnt/data/payroll/timesheets/excel/
# If empty, re-copy the files
```

### Issue: PVC stuck in "Pending"

**Solution:**
```bash
# Check PV status
kubectl get pv,pvc -n payroll-system

# If PV is not created, reapply:
kubectl delete -f k8s/03-persistent-volume.yaml
kubectl apply -f k8s/03-persistent-volume.yaml
```

---

## 📊 Monitoring Commands

```bash
# View all resources
kubectl get all -n payroll-system

# Watch pod status
kubectl get pods -n payroll-system --watch

# View detailed logs
kubectl logs -n payroll-system -l app=agentic-payroll --tail=100

# Check resource usage
kubectl top pods -n payroll-system

# View events
kubectl get events -n payroll-system --sort-by='.lastTimestamp'
```

---

## 🧹 Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/

# Stop Minikube
minikube stop

# (Optional) Delete Minikube cluster
minikube delete
```

---

## 📚 Additional Resources

- **Full Deployment Guide:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **System Architecture:** [README.md](./README.md)
- **CI/CD Pipeline:** [.github/workflows/ci-cd.yaml](./.github/workflows/ci-cd.yaml)

## 🆘 Need Help?

- Check logs: `kubectl logs -n payroll-system -l app=agentic-payroll`
- Describe resources: `kubectl describe pod <pod-name> -n payroll-system`
- View events: `kubectl get events -n payroll-system`
- Minikube dashboard: `minikube dashboard`

---

**Congratulations!** 🎊 You've successfully deployed an agentic AI system to Kubernetes!
