output "sns_topic_arn" {
  description = "ARN of the SNS topic"
  value       = aws_sns_topic.guardduty_sns_topic.arn
}

output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = aws_guardduty_detector.gd_detector.id
}

output "slack_api_endpoint" {
  value = "${aws_apigatewayv2_api.slack_isolation_api.api_endpoint}/slack/interaction"
}
