terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Configure backend after running bootstrap/state.
  # backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}
