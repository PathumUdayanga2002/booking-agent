# EKS Dev Environment Configuration

# ============================================
# Backend Configuration
# ============================================

# Before first `terraform init`, run:
#   terraform init \
#     -backend-config="bucket=YOUR_STATE_BUCKET" \
#     -backend-config="key=envs/eks-dev/terraform.tfstate" \
#     -backend-config="region=us-east-1" \
#     -backend-config="dynamodb_table=YOUR_LOCK_TABLE"

# Or create a backend config file:
#   cat > backend-config.tfbackend << EOF
#   bucket = "booking-app-state-ACCOUNT_ID"
#   key = "envs/eks-dev/terraform.tfstate"
#   region = "us-east-1"
#   dynamodb_table = "booking-app-tflock"
#   encrypt = true
#   EOF
#
#   terraform init -backend-config=backend-config.tfbackend

# ============================================
# EKS Configuration
# ============================================

# All values can be overridden via:
#   terraform apply -var="kubernetes_version=1.30"
#
# Or create a .tfvars file:
#   cat > terraform.tfvars << EOF
#   aws_region = "us-east-1"
#   kubernetes_version = "1.29"
#   EOF

# ============================================
# Cost Optimization Tips
# ============================================

# 1. Start with Fargate for lower cost:
#    - Set node_scaling config to minimal
#    - Use Fargate profiles for less-critical workloads
#
# 2. Reserved Instances (RI) for long-term:
#    - 1-year RI can save ~30-40% on compute
#
# 3. Monitor with Cost Explorer
