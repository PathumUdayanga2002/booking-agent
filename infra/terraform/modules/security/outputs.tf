output "control_plane_instance_profile_name" {
  description = "Control-plane instance profile name"
  value       = aws_iam_instance_profile.control_plane.name
}

output "worker_instance_profile_name" {
  description = "Worker instance profile name"
  value       = aws_iam_instance_profile.worker.name
}

output "control_plane_role_arn" {
  description = "Control-plane role ARN"
  value       = aws_iam_role.control_plane.arn
}

output "worker_role_arn" {
  description = "Worker role ARN"
  value       = aws_iam_role.worker.arn
}

output "worker_rag_s3_policy_arn" {
  description = "Worker S3 RAG policy ARN"
  value       = aws_iam_policy.worker_rag_s3.arn
}
