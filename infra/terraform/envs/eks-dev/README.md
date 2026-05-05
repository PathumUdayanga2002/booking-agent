# Phase 3 EKS Environment

This is the **simpler managed Kubernetes option** using AWS EKS.

## Comparison: EKS vs Manual kubeadm

### EKS (This directory)
- AWS manages the control plane (etcd, API server, scheduler, etc.)
- You manage only the worker nodes
- Automatic patching and updates
- Better AWS integration (IAM, CloudWatch, ALB/NLB)
- **Ideal for beginners and production**
- Higher cost due to AWS management fee (~$0.10/hour)

### Manual kubeadm (../dev)
- You manage everything (control plane + workers)
- More learning opportunity
- Lower cost
- More operational complexity
- Good for understanding Kubernetes internals

## Cost Estimate (AWS Free Tier eligible for 12 months)

- EKS cluster: $0.10/hour (~$73/month)
- t3.medium EC2 nodes (2-4): $0.04/hour each (~$60/month for 2 nodes)
- Storage, data transfer, ALB: ~$15-30/month
- **Total: ~$150-170/month** (still under $200 budget if you keep minimal resources)

## Quick Start

```bash
cd infra/terraform/envs/eks-dev
terraform init
terraform apply
```

## Getting kubeconfig after deployment

```bash
aws eks update-kubeconfig \
  --name booking-app-eks-dev \
  --region us-east-1
kubectl get nodes
```

## Deploy Kubernetes manifests

```bash
kubectl apply -k ../../platform/kubernetes/overlays/dev
```

## Cleanup

```bash
terraform destroy
```

## Learning Path

1. **Week 1-2:** Use EKS for quick learning and deployment
2. **Week 3-4:** Study the manual kubeadm setup in `../dev` to understand control plane
3. **Week 5+:** Build your own kubeadm cluster for advanced understanding
