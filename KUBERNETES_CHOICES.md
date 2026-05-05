# EKS vs Manual kubeadm: Complete Comparison Guide

## Architecture Overview

You now have **two parallel Kubernetes paths** in your infrastructure:

### Option 1: EKS (AWS Managed) - RECOMMENDED FOR BEGINNERS
**Location:** `infra/terraform/envs/eks-dev/`

```
┌─────────────────────────────────────────┐
│          AWS (Managed)                  │
├─────────────────────────────────────────┤
│  EKS Control Plane                      │  ← AWS handles this
│  (API Server, Scheduler, etcd)          │
├─────────────────────────────────────────┤
│  Your VPC                               │
│  ├─ EC2 Worker Nodes (t3.medium)        │  ← You manage these
│  └─ Auto Scaling Group                  │
├─────────────────────────────────────────┤
│  Networking                             │
│  ├─ VPC + Subnets                       │
│  └─ Security Groups                     │
├─────────────────────────────────────────┤
│  Storage                                │
│  ├─ S3 (RAG documents)                  │
│  └─ EBS (persistent volumes)            │
└─────────────────────────────────────────┘
```

### Option 2: Manual kubeadm - LEARNING & SELF-MANAGED
**Location:** `infra/terraform/envs/dev/`

```
┌──────────────────────────────────┐
│  You Manage Everything           │
├──────────────────────────────────┤
│  Control Plane (EC2)             │
│  ├─ API Server                   │
│  ├─ Scheduler                    │
│  ├─ Controller Manager           │
│  └─ etcd                         │
├──────────────────────────────────┤
│  Worker Nodes (EC2)              │
│  ├─ Kubelet                      │
│  └─ Container Runtime            │
├──────────────────────────────────┤
│  Networking (calico/flannel)     │
├──────────────────────────────────┤
│  Storage (EBS)                   │
└──────────────────────────────────┘
```

## Detailed Comparison

| Feature | EKS | Manual kubeadm |
|---------|-----|-----------------|
| **Control Plane Management** | AWS managed (patched automatically) | You manage (manual patching) |
| **Kubernetes Upgrades** | One-click upgrades by AWS | Manual cluster upgrade process |
| **Setup Time** | 5-10 minutes | 30-60 minutes |
| **Learning Curve** | Beginner-friendly | Intermediate/Advanced |
| **Monthly Cost (2 nodes)** | ~$170 (~$0.10/hr cluster + compute) | ~$60-80 (compute only) |
| **AWS Integration** | Native IAM, CloudWatch, ALB/NLB | Requires additional setup |
| **High Availability** | Multi-AZ by default | Configure yourself |
| **Compliance/Audit** | Built-in AWS compliance | Manual implementation |
| **Monitoring** | CloudWatch included | Install Prometheus/Grafana |
| **When You'd Use It** | Production, beginners | Learning, cost-sensitive labs |

## Cost Breakdown

### EKS Setup (eks-dev)
```
EKS Cluster:        $0.10/hour       = $73/month
t3.medium × 2:      $0.08/hour       = $60/month  
NAT Gateway:        $0.045/hour      = $33/month
Data Transfer:      ~$5-10/month
Storage (minimal):  ~$5/month
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:              ~$170/month
```

### Manual kubeadm Setup (dev)
```
t3.medium × 3-4:    $0.04-0.05/hour × count = $30-60/month
NAT Gateway:        $0.045/hour      = $33/month
Storage (minimal):  ~$5/month
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:              ~$60-100/month
```

## Recommended Learning Path

### Week 1-2: Start with EKS
**Goal:** Deploy your booking app and learn Kubernetes concepts

```bash
cd infra/terraform/envs/eks-dev
terraform init \
  -backend-config="bucket=your-state-bucket" \
  -backend-config="key=envs/eks-dev/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=your-lock-table"

terraform plan
terraform apply

# Configure kubectl
aws eks update-kubeconfig \
  --name booking-app-eks-dev \
  --region us-east-1

# Deploy your app
kubectl apply -k ../../platform/kubernetes/overlays/dev
kubectl get pods -n booking-app
```

**What you'll learn:**
- Kubernetes pods, services, ingress
- Deployments and StatefulSets
- Persistent volumes with EBS
- IRSA (IAM Roles for Service Accounts)

### Week 3-4: Study Manual kubeadm
**Goal:** Understand how Kubernetes actually works

```bash
# Review existing manual setup
cat infra/terraform/envs/dev/README.md
cat docs/runbooks/phase-2-kubeadm-hardening.md

# Study the kubeadm bootstrap
cat infra/terraform/envs/dev/userdata/control-plane.sh.tftpl
cat infra/terraform/envs/dev/userdata/worker.sh.tftpl
```

**What you'll learn:**
- kubeadm initialization process
- Kubernetes component architecture
- CNI (Container Network Interface) setup
- Certificate management
- etcd database fundamentals

### Week 5+: Deploy Manual kubeadm (Optional)
**Goal:** Build it yourself for deep understanding

```bash
cd infra/terraform/envs/dev
terraform apply
# Watch it bootstrap... this takes 10-15 minutes
```

## Migration Path (if needed later)

If you start with EKS and want to switch to manual:

1. Export your apps from EKS
```bash
kubectl get all -A -o yaml > backup.yaml
```

2. Destroy EKS
```bash
cd infra/terraform/envs/eks-dev
terraform destroy
```

3. Deploy manual kubeadm
```bash
cd infra/terraform/envs/dev
terraform apply
```

4. Restore your apps
```bash
kubectl apply -f backup.yaml
```

## Running Both Simultaneously (for comparison)

You can run both environments at once to compare, but it will double your AWS costs:

```bash
# Terminal 1
cd infra/terraform/envs/eks-dev
terraform apply

# Terminal 2
cd infra/terraform/envs/dev
terraform apply

# Now you have two separate clusters!
# Configure kubectl to switch between them:
kubectl config get-contexts
kubectl config use-context booking-app-eks-dev
kubectl config use-context booking-app-dev
```

## Key Decisions

### Choose EKS If You:
- ✅ Want to focus on deploying applications
- ✅ Need production-ready setup quickly
- ✅ Prefer AWS to handle control plane patching
- ✅ Need AWS IAM integration for pods
- ✅ Have budget for AWS management fee
- ✅ Want compliance/audit trails built-in

### Choose Manual kubeadm If You:
- ✅ Want to learn Kubernetes internals
- ✅ Have a tight budget (no AWS management fee)
- ✅ Need complete control over every component
- ✅ Want to study cluster bootstrap process
- ✅ Running in non-AWS environments later
- ✅ Have time to manage control plane

## Next Steps

1. **Pick your starting point:**
   ```bash
   # Start here (easier)
   cd infra/terraform/envs/eks-dev
   
   # OR start here (learning-focused)
   cd infra/terraform/envs/dev
   ```

2. **Initialize and deploy:**
   ```bash
   terraform init -backend-config="..." 
   terraform plan
   terraform apply
   ```

3. **Verify your cluster:**
   ```bash
   aws eks describe-cluster --name booking-app-eks-dev
   kubectl get nodes
   kubectl get pods -n booking-app
   ```

4. **Read the runbooks:**
   - EKS: See `README.md` in eks-dev
   - Manual: See `docs/runbooks/` for detailed guides

## Questions?

- **EKS questions:** AWS EKS documentation
- **kubeadm questions:** kubernetes.io/docs/setup/production-environment/tools/kubeadm/
- **Your app questions:** Check `platform/kubernetes/base/`
