# EKS Module

Creates an AWS EKS cluster with optional add-ons.

## Features

- EKS cluster creation with configurable version
- IAM role for cluster operations
- Security group configuration
- Optional add-ons (VPC CNI, CoreDNS, kube-proxy, EBS CSI)
- OIDC provider for IRSA (IAM Roles for Service Accounts)

## Usage

```hcl
module "eks" {
  source = "../../modules/eks"

  cluster_name    = "booking-app-eks"
  kubernetes_version = "1.29"
  vpc_id          = module.network.vpc_id
  subnet_ids      = module.network.private_subnet_ids
  
  enable_addons = {
    vpc_cni = true
    ebs_csi = true
    coredns = true
  }
  
  tags = local.merged_tags
}
```

## Outputs

- cluster_name: EKS cluster name
- cluster_arn: Cluster ARN
- cluster_endpoint: Cluster API endpoint
- cluster_ca_cert: Cluster CA certificate
- oidc_provider_arn: OIDC provider for IRSA
