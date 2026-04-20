variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "kms_key_arn" {
  description = "Optional KMS key ARN for bucket encryption"
  type        = string
  default     = null
}

variable "force_destroy" {
  description = "Allow bucket deletion with objects"
  type        = bool
  default     = false
}

variable "enable_lifecycle" {
  description = "Enable lifecycle expiration policy"
  type        = bool
  default     = true
}

variable "expiration_days" {
  description = "Days before object expiration"
  type        = number
  default     = 180
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
