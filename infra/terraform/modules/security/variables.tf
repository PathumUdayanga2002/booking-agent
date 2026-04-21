variable "name" {
  description = "Name prefix for IAM resources"
  type        = string
}

variable "rag_bucket_arn" {
  description = "ARN of the RAG source S3 bucket"
  type        = string
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
