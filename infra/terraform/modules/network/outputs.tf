output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_route_table_id" {
  description = "Public route table ID"
  value       = aws_route_table.public.id
}

output "private_route_table_id" {
  description = "Private route table ID"
  value       = aws_route_table.private.id
}

output "vpc_endpoint_security_group_id" {
  description = "VPC endpoint interface security group ID"
  value       = var.enable_vpc_endpoints ? aws_security_group.vpce[0].id : null
}

output "s3_gateway_endpoint_id" {
  description = "S3 gateway endpoint ID"
  value       = var.enable_vpc_endpoints && var.enable_s3_gateway_endpoint ? aws_vpc_endpoint.s3_gateway[0].id : null
}

output "interface_endpoint_ids" {
  description = "Map of interface endpoint IDs by service"
  value       = { for service, endpoint in aws_vpc_endpoint.interface : service => endpoint.id }
}
