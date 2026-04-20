# Terraform Bootstrap Runbook

## Purpose

Create remote Terraform state resources once per account/region.

## Steps

1. Copy `infra/terraform/bootstrap/state/terraform.tfvars.example` to `terraform.tfvars`.
2. Set unique `state_bucket_name` and `lock_table_name`.
3. Run:

```powershell
cd infra/terraform/bootstrap/state
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

4. Configure S3 backend in each environment after bootstrap is complete.

## Validation

- S3 bucket exists and versioning is enabled.
- DynamoDB lock table exists.
- Public access block is enabled on state bucket.
