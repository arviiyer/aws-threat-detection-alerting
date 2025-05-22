variable "aws_region" {
  description = "AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "email_address" {
  description = "Email address to receive SNS notifications"
  type        = string
  default     = "rbarvind04@gmail.com"
}

variable "slack_bot_token" {
  description = "Slack Bot OAuth for chat.postMessage"
  type        = string
  sensitive   = true
}

variable "slack_signing_secret" {
  description = "Slack app signing secret for verifying requests"
  type        = string
  sensitive   = true
}

variable "vpc_id" {
  description = "The VPC ID to create the quarantine security group in"
  type        = string
}
