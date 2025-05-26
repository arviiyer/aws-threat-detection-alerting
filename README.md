# AWS Threat Detection & Response Orchestrator

This repository implements a modern, serverless security automation framework using AWS GuardDuty, Amazon EventBridge, AWS Lambda, Amazon SNS, Amazon API Gateway, and Slack. Built and deployed with Terraform, the solution is designed to detect threats in your AWS environment, notify your team in real-time, and enable one-click EC2 isolation directly from Slack.

> This solution is a cloud-native incident response pipeline that combines AWS GuardDuty, Slack, and Terraform to deliver real-time alerts and interactive remediation of EC2-based threats — all from your chat window.

## 🔧 Key Features

- 🚨 Automated detection of high-severity GuardDuty findings
- 🧠 EC2-aware alert enrichment with tagging and IP context
- 💬 Slack notifications with one-click quarantine
- 🛡️ Secure Slack-to-AWS communication via API Gateway & HMAC verification
- 📧 Multi-channel alerting (SNS + Slack)
- ⚙️ Fully infrastructure-as-code via Terraform

## Table of Contents

* [Overview](#overview)
* [Architecture](#architecture)
* [Prerequisites](#prerequisites)
* [Deployment Steps](#deployment-steps)
* [Slack App Configuration](#slack-app-configuration)
* [Testing the Setup](#testing-the-setup)
* [Cleanup](#cleanup)
* [Cost Considerations](#cost-considerations)
* [Conclusion](#conclusion)
* [References](#references)
* [License](#license)
* [Contact](#contact)

## Overview

This project implements a complete detection and response workflow that:

* Enables **AWS GuardDuty** to detect suspicious activity.
* Uses **Amazon EventBridge** to route high-severity findings.
* Invokes a **Lambda function** to:

  * Enrich GuardDuty findings with EC2 metadata.
  * Send alerts to a **Slack channel** and **Amazon SNS**.
  * Provide a one-click quarantine action via Slack.
* Provides a secure Slack-to-AWS bridge via **API Gateway**, which forwards interactive requests to another Lambda function.
* Invokes a second **Lambda function** to isolate EC2 instances using a quarantine security group.
* Verifies all Slack interactions using HMAC signature validation.
* Deploys the solution using **Terraform** and packages Lambda functions using a lightweight build script.

## Architecture

![Architecture Diagram](images/architecture_diagram.png)

### Components

1. **AWS GuardDuty**

   * Continuously monitors AWS resources for threats.

2. **Amazon EventBridge**

   * Filters and routes high-severity GuardDuty findings to a Lambda function.

3. **Lambda: guardduty\_formatter**

   * Enriches findings with EC2 metadata (if available).
   * Sends alerts to Slack and SNS.
   * Includes interactive Slack buttons for remediation.
   * Gracefully handles non-EC2 findings.

4. **Amazon SNS**

   * Delivers notifications to additional endpoints such as email.

5. **Slack Integration**

   * Slack bot posts enriched alerts.
   * Interactive buttons allow one-click EC2 quarantine.

6. **Amazon API Gateway (HTTP)**

   * Exposes a secure endpoint to receive Slack interactive messages.
   * Forwards valid requests to the isolation Lambda function.

7. **Lambda: ec2\_isolation\_handler**

   * Validates Slack request signatures.
   * Applies quarantine security group to EC2 instances.
   * Posts a success message back to Slack.

8. **IAM Roles and Policies**

   * Grant least-privilege permissions to Lambda functions.

9. **CloudWatch Logs**

   * Captures all Lambda execution logs for troubleshooting.

10. **Build Script (`build.sh`)**

    * Packages each Lambda function with dependencies for deployment.

## Prerequisites

* AWS account with permissions to deploy GuardDuty, Lambda, SNS, API Gateway, and IAM roles.
* AWS CLI installed and configured.
* Terraform installed.
* Slack workspace with:

  * Slack Bot token
  * Signing secret
  * A channel for alert posting

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/arviiyer/aws-threat-detection-alerting.git
cd aws-threat-detection-alerting
```

### 2. Prepare `terraform.tfvars`

Create a file named `terraform.tfvars` in the project root directory and populate it with your values:

```hcl
slack_bot_token      = "xoxb-your-slack-bot-token"
slack_signing_secret = "your-slack-signing-secret"
vpc_id               = "vpc-xxxxxxxxxxxxxx"
```

> 🔒 Do not commit this file. It contains sensitive credentials and should be listed in your `.gitignore`.

### 3. Package Lambda Functions

```bash
./build.sh
```

Creates:

* `guardduty_formatter.zip`
* `ec2_isolation_handler.zip`

These are referenced by Terraform during deployment.

### 4. Initialize and Apply Terraform

```bash
terraform init
terraform plan
terraform apply
```

> ✅ Confirm with `yes` when prompted.

![Terraform Output](images/tfa_output.jpg)

### 5. Confirm SNS Email Subscription

Check your inbox and click the **"Confirm subscription"** link from AWS.

## Slack App Configuration

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and create a new app.
2. Enable **Interactivity** and set the Request URL to your API Gateway endpoint (output from Terraform).
3. Add **chat\:write**, **commands**, and **incoming-webhook** scopes.
4. Install the app to your workspace.
5. Use the bot token and signing secret in your `terraform.tfvars` file.

![Slack App Configuration](images/slack_app_configuration.jpg)

## Testing the Setup

### 1. Simulate a Finding

```bash
aws guardduty create-sample-findings \
  --detector-id $(terraform output -raw guardduty_detector_id) \
  --finding-types "Recon:EC2/PortProbeUnprotectedPort"
```

Or use the AWS Console to generate sample findings.

### 2. Slack Alert

* Check the channel for a new message.
* If EC2-related, it will contain instance details and a quarantine button.

![Slack Alert Message](images/slack_alert_message.jpg)

> Slack alert with enriched EC2 metadata and quarantine button

### 3. One-Click Quarantine

* Clicking the button sends a secure request to API Gateway.
* The isolation Lambda updates the instance SG.
* Slack confirms successful isolation.

![Slack Button Interaction](images/slack_button_interaction.jpg)

> Slack confirms the EC2 instance has been isolated

## Cleanup

```bash
terraform destroy
```

> 🧹 Removes all deployed resources to prevent ongoing costs.

## Cost Considerations

* **GuardDuty**: Free for 30 days; usage-based after.
* **Lambda**: Free tier covers most use cases.
* **SNS**: Low-cost for email notifications.
* **API Gateway**: Based on request volume.
* **Slack**: Free plan supports this integration.

> 💡 Always check your AWS billing dashboard.

## Conclusion

This project delivers a fast, automated, and secure cloud-native incident response system:

* 🔍 Real-time GuardDuty findings
* 💬 Slack alerts with actionable context
* 🖱 One-click EC2 quarantine
* 🔐 Verified, secure Slack interactions
* ⚙️ Fully automated via Terraform

Future improvements could include tagging support, audit logging via DynamoDB, or integration with AWS Security Hub.

## References

* [AWS GuardDuty](https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html)
* [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
* [Amazon EventBridge](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html)
* [Amazon SNS](https://docs.aws.amazon.com/sns/latest/dg/welcome.html)
* [API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html)
* [Slack API](https://api.slack.com/)
* [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

## License

MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

📧 [rbarvind04@gmail.com](mailto:rbarvind04@gmail.com)

> **Disclaimer**: Ensure appropriate permissions and compliance review before production deployment.
