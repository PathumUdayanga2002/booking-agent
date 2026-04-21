# Phase 2.5 Hardening Checklist

## Objective

Complete security and private-network hardening for Terraform-based EC2 Kubernetes foundation.

## Completed Controls

1. IAM role split by node role:
- separate control-plane role/profile
- separate worker role/profile

2. Least-privilege RAG S3 access:
- worker role can list/read/write only the configured RAG bucket

3. VPC endpoint controls:
- optional S3 gateway endpoint
- optional interface endpoints (ECR, SSM, CloudWatch Logs family)

4. NodePort exposure hardening:
- optional NodePort ingress from explicit CIDRs
- preferred optional NodePort ingress from ingress NLB security group

## Validation Steps

1. Terraform validation:

```powershell
cd infra/terraform/envs/dev
terraform init -backend=false
terraform validate
```

2. Plan review for IAM and SG changes:

```powershell
terraform plan -var-file="terraform.tfvars"
```

3. Security review points:
- verify worker policy only targets RAG bucket ARN and ARN/*
- verify control-plane role does not include RAG object permissions
- verify NodePort is not open to 0.0.0.0/0 unless explicitly intended

## Recommended Next Steps

1. Add a dedicated module for ingress/NLB provisioning and pass SG IDs directly from Terraform outputs.
2. Add VPC endpoint policy restrictions where required.
3. Add AWS Config and GuardDuty integration in later hardening phases.
