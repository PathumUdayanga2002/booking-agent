# Terraform Infrastructure

This directory contains AWS infrastructure as code for the booking platform.

## Layout

- `bootstrap/state` - creates remote Terraform state resources (S3 + DynamoDB lock table)
- `modules/network` - VPC, subnets, routing, and optional NAT
- `modules/security` - IAM roles/profiles and least-privilege policies for EC2 node groups
- `modules/storage` - S3 bucket for RAG source documents
- `envs/dev` - development environment composition
- `envs/staging` - staging environment composition (to be implemented)
- `envs/prod` - production environment composition (to be implemented)

## Quick Start (dev)

1. Bootstrap state resources first.
2. Initialize and plan `envs/dev`.
3. Apply after review.

Example:

```powershell
cd infra/terraform/bootstrap/state
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"

cd ../../envs/dev
terraform init
terraform plan -var-file="terraform.tfvars"
```
