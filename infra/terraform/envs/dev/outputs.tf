output "vpc_id" {
  description = "VPC ID"
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.network.private_subnet_ids
}

output "rag_bucket_name" {
  description = "RAG document bucket name"
  value       = module.rag_storage.bucket_name
}

output "control_plane_asg_name" {
  description = "Control-plane autoscaling group name"
  value       = module.compute.control_plane_asg_name
}

output "worker_asg_name" {
  description = "Worker autoscaling group name"
  value       = module.compute.worker_asg_name
}

output "control_plane_security_group_id" {
  description = "Control-plane security group ID"
  value       = module.compute.control_plane_security_group_id
}

output "worker_security_group_id" {
  description = "Worker security group ID"
  value       = module.compute.worker_security_group_id
}

output "vpc_endpoint_security_group_id" {
  description = "VPC endpoint security group ID"
  value       = module.network.vpc_endpoint_security_group_id
}

output "s3_gateway_endpoint_id" {
  description = "S3 gateway endpoint ID"
  value       = module.network.s3_gateway_endpoint_id
}

output "interface_endpoint_ids" {
  description = "Map of interface endpoint IDs"
  value       = module.network.interface_endpoint_ids
}

output "control_plane_instance_profile_name" {
  description = "Control-plane IAM instance profile name"
  value       = module.security.control_plane_instance_profile_name
}

output "worker_instance_profile_name" {
  description = "Worker IAM instance profile name"
  value       = module.security.worker_instance_profile_name
}

output "control_plane_role_arn" {
  description = "Control-plane IAM role ARN"
  value       = module.security.control_plane_role_arn
}

output "worker_role_arn" {
  description = "Worker IAM role ARN"
  value       = module.security.worker_role_arn
}

output "worker_rag_s3_policy_arn" {
  description = "Attached worker policy ARN for RAG S3 access"
  value       = module.security.worker_rag_s3_policy_arn
}
