provider "aws" {
  region = var.aws_region
}

# enable guardduty
resource "aws_guardduty_detector" "gd_detector" {
  enable = true
}

# create sns topic
resource "aws_sns_topic" "guardduty_sns_topic" {
  name = "guardduty-high-severity-topic"
}

# create sns subscription
resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.guardduty_sns_topic.arn
  protocol  = "email"
  endpoint  = var.email_address
}

# iam role for lambda
resource "aws_iam_role" "lambda_role" {
  name = "guardduty_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# iam policy attachment for lambda logging
resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# iam policy for lambda to publish to sns
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

# iam policy for ec2 describeinstances access
resource "aws_iam_policy" "lambda_ec2_describe_policy" {
  name = "lambda_ec2_describe_policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = [
        "ec2:DescribeInstances"
      ],
      Resource = "*"
    }]
  })
}

# iam policy for EC2 Isolation
resource "aws_iam_policy" "lambda_ec2_isolate_policy" {
  name = "lambda_ec2_isolate_policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = [
        "ec2:ModifyInstanceAttribute"
      ],
      Resource = "*"
    }]
  })
}

#attach ec2 isolation policy to lambda role
resource "aws_iam_role_policy_attachment" "lambda_ec2_isolate" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_ec2_isolate_policy.arn
}

# attach the ec2 describe policy to lambda role
resource "aws_iam_role_policy_attachment" "lambda_ec2_describe" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_ec2_describe_policy.arn
}

# attach the sns publish policy to lambda role
resource "aws_iam_role_policy_attachment" "lambda_sns_publish" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_sns_publish_policy.arn
}

# create lambda function for guardduty alert notification, enrichment and formatting
resource "aws_lambda_function" "guardduty_formatter" {
  function_name = "guardduty_formatter"
  role          = aws_iam_role.lambda_role.arn
  handler       = "guardduty_formatter.lambda_handler"
  runtime       = "python3.9"

  filename         = "guardduty_formatter.zip"
  source_code_hash = filebase64sha256("guardduty_formatter.zip")

  environment {
    variables = {
      SNS_TOPIC_ARN   = aws_sns_topic.guardduty_sns_topic.arn
      SLACK_BOT_TOKEN = var.slack_bot_token
    }
  }
}

# create lambda function for ec2 isolation
resource "aws_lambda_function" "ec2_isolation_handler" {
  function_name = "ec2_isolation_handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "ec2_isolation_handler.lambda_handler"
  runtime       = "python3.9"

  filename         = "ec2_isolation_handler.zip"
  source_code_hash = filebase64sha256("ec2_isolation_handler.zip")

  environment {
    variables = {
      QUARANTINE_SG_ID     = aws_security_group.quarantine_sg.id
      SLACK_SIGNING_SECRET = var.slack_signing_secret
    }
  }
}

# eventbridge rule for high-severity findings
resource "aws_cloudwatch_event_rule" "guardduty_high_severity_rule" {
  name        = "guardduty-high-severity-rule"
  description = "capture high-severity guardduty findings"

  event_pattern = jsonencode({
    source        = ["aws.guardduty"],
    "detail-type" = ["guardduty finding"],
    detail = {
      severity = [{ numeric = [">", 6.9] }]
    }
  })
}

# permission for eventbridge to invoke lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "allowexecutionfromeventbridge"
  action        = "lambda:invokefunction"
  function_name = aws_lambda_function.guardduty_formatter.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.guardduty_high_severity_rule.arn
}

# eventbridge target to lambda
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.guardduty_high_severity_rule.name
  target_id = "guardduty-lambda"
  arn       = aws_lambda_function.guardduty_formatter.arn
}

# isolation security group
resource "aws_security_group" "quarantine_sg" {
  name        = "quarantine-sg"
  description = "Security group that blocks all inbound and outbound traffic"
  vpc_id      = var.vpc_id # Using default vpc as the variable for now

  # No ingress or egress rules here which blocks all traffic by default
}
