output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_version" {
  description = "EKS cluster version"
  value       = aws_eks_cluster.main.version
}

output "cluster_ca_certificate" {
  description = "Base64 encoded cluster CA certificate"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "oidc_provider_arn" {
  description = "ARN of OIDC provider for IRSA"
  value       = aws_iam_openid_connect_provider.cluster.arn
}

output "oidc_provider_url" {
  description = "OIDC provider URL"
  value       = aws_iam_openid_connect_provider.cluster.url
}

output "cluster_security_group_id" {
  description = "Cluster security group ID"
  value       = try(aws_security_group.cluster[0].id, var.cluster_security_group_id)
}

output "node_security_group_id" {
  description = "Node security group ID"
  value       = aws_security_group.node.id
}

output "node_role_arn" {
  description = "Node IAM role ARN"
  value       = aws_iam_role.node_role.arn
}

output "cluster_role_arn" {
  description = "Cluster IAM role ARN"
  value       = aws_iam_role.cluster_role.arn
}
