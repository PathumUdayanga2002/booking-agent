# AWS Networking Baseline (No EKS)

## Goals

- Keep workloads private by default.
- Expose only ingress entrypoints publicly.
- Minimize blast radius with subnet and security group segmentation.

## Baseline Topology

- VPC per environment or strict subnet segmentation in one VPC.
- Public subnets:
  - NLB and ingress entrypoints only.
- Private subnets:
  - Kubernetes control-plane and worker nodes.
  - qdrant StatefulSet storage access.
- NAT:
  - Optional NAT gateway in dev (off by default for budget).

## Security Controls

- SSM Session Manager for administration.
- Restrictive security groups per tier.
- Bucket and database access by explicit IAM policy only.
- VPC endpoints for S3/ECR/CloudWatch/SSM when enabled.
