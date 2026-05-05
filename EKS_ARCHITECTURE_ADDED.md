# Architecture Addition Summary

## What Was Added (May 5, 2026)

You now have **two complete Kubernetes deployment paths** in your infrastructure:

### New: EKS Managed Kubernetes

**Location:** `infra/terraform/envs/eks-dev/`

✅ **AWS-managed control plane** - AWS handles etcd, API server, scheduler
✅ **Auto-scaling worker nodes** - t3.medium instances (2-4 nodes)
✅ **CloudWatch logging** - Control plane logs automatically collected
✅ **IRSA support** - IAM Roles for Service Accounts (pods can use AWS APIs)
✅ **EBS CSI driver** - Persistent volumes built-in
✅ **Simple upgrades** - One AWS API call to upgrade Kubernetes version

**New Files:**
- `infra/terraform/modules/eks/` - EKS cluster module (main.tf, variables.tf, outputs.tf, README.md)
- `infra/terraform/envs/eks-dev/` - Environment configuration (main.tf, variables.tf, README.md, CONFIGURATION.md)
- `KUBERNETES_CHOICES.md` - Comparison and learning guide (in root)

### Existing: Manual kubeadm (NOT MODIFIED)

**Location:** `infra/terraform/envs/dev/`

✅ Still available for learning
✅ Complete control over everything
✅ Lower AWS cost (no EKS management fee)
✅ Study the bootstrap process in userdata scripts

---

## Quick Start Comparison

### START WITH EKS (Recommended for Beginners)

```bash
# 1. Navigate to EKS environment
cd infra/terraform/envs/eks-dev

# 2. Initialize Terraform backend
terraform init \
  -backend-config="bucket=YOUR_STATE_BUCKET" \
  -backend-config="key=envs/eks-dev/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=YOUR_LOCK_TABLE"

# 3. Plan and apply
terraform plan
terraform apply

# 4. Get kubeconfig
aws eks update-kubeconfig --name booking-app-eks-dev --region us-east-1

# 5. Deploy your app
kubectl apply -k ../../platform/kubernetes/overlays/dev

# 6. Monitor
kubectl get pods -n booking-app
kubectl logs -f deployment/backend -n booking-app
```

**Time to running:** ~10-15 minutes

### LEARN WITH MANUAL KUBEADM (For Later Study)

```bash
# Same steps as before - nothing changed!
cd infra/terraform/envs/dev
terraform apply
```

**Time to running:** ~30-45 minutes (because kubeadm bootstrap takes longer)

---

## Cost Estimates

| Setup | Monthly Cost | Best For |
|-------|--------------|----------|
| **EKS** | ~$170 | Production, quick deployment, AWS native |
| **kubeadm** | ~$80 | Learning, cost-sensitive, self-managed |
| **Both** | ~$250 | Comparison and learning |

**AWS Free Tier:** EKS is eligible; EC2 instances get 750 hours/month free for 12 months

---

## Directory Structure

```
infra/terraform/
├── bootstrap/                      # Remote state setup
│   └── state/
├── modules/
│   ├── network/                    # VPC, subnets, NAT (shared)
│   ├── storage/                    # S3 RAG bucket (shared)
│   ├── compute/                    # EC2 for kubeadm (manual setup)
│   ├── security/                   # IAM roles/policies (manual setup)
│   └── eks/                        # ← NEW: EKS cluster module
├── envs/
│   ├── dev/                        # Manual kubeadm setup (existing)
│   └── eks-dev/                    # ← NEW: EKS managed setup
└── README.md
```

---

## Key Features of EKS Setup

### 1. Network Reuse
- Uses same network module as manual setup
- Same VPC/subnets for consistency
- Easy to migrate apps between both clusters

### 2. IAM & Security
- Pod IAM roles (IRSA) for fine-grained permissions
- Worker node S3 access for RAG documents
- Security groups for cluster/node traffic

### 3. Add-ons Included
- **VPC CNI** - Pod networking
- **CoreDNS** - Service discovery
- **kube-proxy** - Service networking
- **EBS CSI Driver** - Persistent volumes

### 4. Logging
- Control plane logs to CloudWatch
- Audit logging enabled
- 30-day retention (configurable)

### 5. Auto-Scaling
- Node group with 1-4 nodes
- CPU-based scaling via HPA (Horizontal Pod Autoscaler)

---

## Migration Between Setups

If you start with EKS and later want to use manual kubeadm:

```bash
# Export from EKS
kubectl get all -A -o yaml > apps-backup.yaml

# Destroy EKS
cd infra/terraform/envs/eks-dev
terraform destroy

# Deploy manual
cd ../dev
terraform apply

# Restore apps
kubectl apply -f apps-backup.yaml
```

---

## What's Next?

### Option A: Deploy EKS Now (Beginner Path - Recommended)
1. Read: `infra/terraform/envs/eks-dev/README.md`
2. Configure backend state bucket
3. Run: `terraform apply`
4. Deploy apps: `kubectl apply -k platform/kubernetes/overlays/dev`

### Option B: Study Manual Setup First (Learning Path)
1. Read: `KUBERNETES_CHOICES.md` (detailed comparison)
2. Review: `infra/terraform/envs/dev/README.md`
3. Study: `docs/runbooks/phase-2-kubeadm-hardening.md`
4. Then deploy one or both

### Option C: Run Both (Comparison Lab)
1. Deploy EKS to one cluster
2. Deploy manual to another
3. Compare kubectl commands, logs, and management
4. See differences in monitoring and AWS integration

---

## Documentation Files

- **KUBERNETES_CHOICES.md** - Full comparison, learning path, cost breakdown
- **infra/terraform/envs/eks-dev/README.md** - EKS quick start
- **infra/terraform/envs/eks-dev/CONFIGURATION.md** - Backend setup notes
- **infra/terraform/modules/eks/README.md** - EKS module details
- **infra/terraform/envs/dev/README.md** - Manual kubeadm (existing)
- **docs/runbooks/phase-2-kubeadm-hardening.md** - Manual setup runbook (existing)

---

## Security Notes

Both setups include:
- IAM least-privilege for worker nodes
- S3 RAG bucket access restricted to nodes only
- Security groups limiting ingress
- CloudWatch audit logging enabled
- VPC endpoints optional (reduce data transfer costs)

---

## Support

For questions about:
- **EKS:** Check AWS EKS documentation or `infra/terraform/modules/eks/README.md`
- **Kubernetes:** Check `platform/kubernetes/base/` or kubernetes.io docs
- **Terraform:** Terraform documentation or the .md files in each directory
- **Architecture:** Read `KUBERNETES_CHOICES.md` for full breakdown

---

## Summary

| Path | Time to Deploy | Cost/Month | Best For |
|------|-----------------|-----------|----------|
| **EKS (eks-dev)** | 10-15 min | ~$170 | Production, beginners |
| **kubeadm (dev)** | 30-45 min | ~$80 | Learning, self-managed |
| **Both** | 60 min | ~$250 | Understanding both systems |

**Recommendation:** Start with EKS, then study manual setup later when ready to go deeper.
