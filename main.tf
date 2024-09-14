provider "aws" {
  region = var.aws_region
}

# Enable GuardDuty
resource "aws_guardduty_detector" "gd_detector" {
  enable = true
}

# Create SNS Topic
resource "aws_sns_topic" "guardduty_sns_topic" {
  name = "guardduty-high-severity-topic"
}

# Create SNS Subscription
resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.guardduty_sns_topic.arn
  protocol  = "email"
  endpoint  = var.email_address
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "guardduty_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# IAM Policy Attachment for Lambda Logging
resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Lambda to Publish to SNS
resource "aws_iam_policy" "lambda_sns_publish_policy" {
  name = "lambda_sns_publish_policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = "sns:Publish",
      Resource = aws_sns_topic.guardduty_sns_topic.arn
    }]
  })
}

# Attach the SNS Publish Policy to Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_sns_publish" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_sns_publish_policy.arn
}

# Create Lambda Function
resource "aws_lambda_function" "guardduty_formatter" {
  function_name = "guardduty_formatter"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"

  filename         = "lambda_function.zip"
  source_code_hash = filebase64sha256("lambda_function.zip")

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.guardduty_sns_topic.arn
    }
  }
}

# EventBridge Rule for High-Severity Findings
resource "aws_cloudwatch_event_rule" "guardduty_high_severity_rule" {
  name        = "guardduty-high-severity-rule"
  description = "Capture high-severity GuardDuty findings"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"],
    "detail-type" = ["GuardDuty Finding"],
    detail      = {
      severity = [{ numeric = [">", 6.9] }]
    }
  })
}

# Permission for EventBridge to Invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.guardduty_formatter.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.guardduty_high_severity_rule.arn
}

# EventBridge Target to Lambda
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.guardduty_high_severity_rule.name
  target_id = "guardduty-lambda"
  arn       = aws_lambda_function.guardduty_formatter.arn
}
