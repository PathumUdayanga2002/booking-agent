output "control_plane_asg_name" {
  description = "Control-plane autoscaling group name"
  value       = aws_autoscaling_group.control_plane.name
}

output "worker_asg_name" {
  description = "Worker autoscaling group name"
  value       = aws_autoscaling_group.worker.name
}

output "control_plane_security_group_id" {
  description = "Control-plane security group ID"
  value       = aws_security_group.control_plane.id
}

output "worker_security_group_id" {
  description = "Worker security group ID"
  value       = aws_security_group.worker.id
}

