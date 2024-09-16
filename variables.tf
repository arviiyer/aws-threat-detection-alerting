variable "aws_region" {
  description = "AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "email_address" {
  description = "Email address to receive SNS notifications"
  type        = string
  default     = "example@email.com"
}
