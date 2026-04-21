variable "name" {
  description = "Name prefix for network resources"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 2
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnet egress"
  type        = bool
  default     = false
}

variable "enable_vpc_endpoints" {
  description = "Enable private VPC endpoints for core AWS services"
  type        = bool
  default     = false
}

variable "enable_s3_gateway_endpoint" {
  description = "Enable S3 Gateway VPC endpoint"
  type        = bool
  default     = true
}

variable "interface_endpoint_services" {
  description = "Interface endpoint service short names (without com.amazonaws.<region> prefix)"
  type        = list(string)
  default = [
    "ecr.api",
    "ecr.dkr",
    "ssm",
    "ec2messages",
    "ssmmessages",
    "logs"
  ]
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
