# AWS GuardDuty Threat Detection & Response

This repository showcases a modern AWS-based threat detection and response solution using AWS GuardDuty, Amazon EventBridge, AWS Lambda, Amazon SNS, and Slack. The solution is deployed via Terraform and is designed to monitor malicious activity in your AWS account, notify your team in real-time, and provide one-click remediation for EC2-related threats.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
- [Testing the Setup](#testing-the-setup)
- [Cleanup](#cleanup)
- [Cost Considerations](#cost-considerations)
- [Conclusion](#conclusion)
- [References](#references)
- [License](#license)
- [Contact](#contact)

## Overview

This project implements a threat detection and response solution that:

- Enables **AWS GuardDuty** to detect suspicious activity.
- Uses **Amazon EventBridge** to route high-severity findings.
- Invokes a **Lambda function** to:
  - Enrich GuardDuty findings with EC2 metadata.
  - Send alerts to a **Slack channel** and **Amazon SNS**.
  - Provide a one-click quarantine action via Slack.
- Invokes a second **Lambda function** to isolate EC2 instances using a quarantine security group.
- Deploys the entire solution using **Terraform** for repeatable infrastructure management.
- Includes a lightweight build script to package Lambda functions for deployment.

## Architecture

![Architecture Diagram](images/architecture_diagram.png)

### Components

1. **AWS GuardDuty**
   - Continuously monitors AWS resources for threats.

2. **Amazon EventBridge**
   - Filters and routes high-severity GuardDuty findings to a Lambda function.

3. **Lambda: guardduty_formatter**
   - Enriches findings with EC2 metadata.
   - Sends messages to Slack and SNS.
   - Includes interactive Slack buttons for remediation.
   - Handles non-EC2 findings gracefully and still reports them.

4. **Lambda: ec2_isolation_handler**
   - Verifies Slack requests (HMAC validation).
   - Isolates EC2 instances by modifying their security groups.
   - Responds in Slack with confirmation.

5. **Amazon SNS**
   - Distributes findings to additional endpoints such as email.

6. **Slack Integration**
   - Slack Bot posts alert messages.
   - Users can click a button to quarantine EC2 instances directly from Slack.

7. **IAM Roles and Policies**
   - Grant least-privilege permissions to Lambda functions.

8. **Build Script (`build.sh`)**
   - Zips each Lambda function for deployment.
   - Minimalist approach; does not currently package dependencies.

## Prerequisites

- AWS account with permissions to deploy GuardDuty, Lambda, SNS, and IAM roles.
- AWS CLI installed and configured.
- Terraform installed.
- Slack workspace with:
  - Slack Bot token
  - Signing secret
  - A channel for alert posting

## Deployment Steps

Follow these steps to deploy the solution:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/aws-guardduty-threat-detection.git
cd aws-guardduty-threat-detection
```

### 2. Prepare `terraform.tfvars`

Create a file named `terraform.tfvars` in the project root directory and populate it with your values:

```hcl
slack_bot_token      = "xoxb-your-slack-bot-token"
slack_signing_secret = "your-slack-signing-secret"
vpc_id               = "vpc-xxxxxxxxxxxxxx"
```

> 🔒 Note: Never commit this file to version control. It contains sensitive credentials and should be listed in your .gitignore.

### 3. Package Lambda Functions

Use the provided `build.sh` script to zip the Lambda function code files:

```bash
./build.sh
```

This script creates two zip archives in the current directory:
- `guardduty_formatter.zip`
- `ec2_isolation_handler.zip`

These archives will be referenced by Terraform during deployment.

> 💡 If you add external Python packages later (e.g., requests, boto3), you'll need to update this script to install dependencies into the zip file structure.

### 4. Initialize and Deploy

After packaging the Lambda functions, use Terraform to deploy the infrastructure:

```bash
terraform init
terraform plan
terraform apply
```

- `terraform init` prepares the working directory and downloads providers.
- `terraform plan` shows what Terraform will do.
- `terraform apply` creates the resources defined in the configuration.

> ✅ When prompted, type `yes` to confirm the deployment.

### 5. Subscribe to SNS

If you’ve configured the SNS topic to send email notifications, check your inbox for a subscription confirmation email from AWS.

1. Open the email with the subject `AWS Notification - Subscription Confirmation`.
2. Click the **“Confirm subscription”** link inside the message.

Once confirmed, you’ll start receiving GuardDuty finding alerts via email as well as Slack.

> 📧 Ensure that the email address used is valid and accessible before deployment.

![SNS Confirmation Email](images/sns_confirmation_email.png)

## Testing the Setup

### 1. Generate Sample GuardDuty Findings

To simulate real-world threats, use AWS to generate sample GuardDuty findings.

#### Using AWS CLI:

```bash
aws guardduty create-sample-findings \
  --detector-id $(terraform output -raw guardduty_detector_id) \
  --finding-types "Recon:EC2/PortProbeUnprotectedPort"
```

Using AWS Console:
1. Go to Amazon GuardDuty in the AWS Console.
2. Select Settings from the sidebar.
3. Click “Generate sample findings”.

![Generate Sample Findings](images/generate_sample_findings.png)

### 2. Verify Slack Notification

- Check your designated Slack channel.

- A message should appear with:
  - Title, severity, description of the finding
  - Enriched EC2 instance info (if applicable)
  - - A `🛑 Quarantine EC2` button if an EC2 instance is involved

![Slack Alert Message](images/slack_guardduty_alert.png)

### 3. Click the Slack Button

- Clicking the button triggers the ec2_isolation_handler Lambda.
- It isolates the instance by applying the quarantine security group.
- A confirmation message will appear in Slack upon success.

![Slack Quarantine Confirmation](images/slack_quarantine_confirmation.png)

## Cleanup

To remove all deployed resources and avoid ongoing charges, run:

```bash
terraform destroy
```

- Review the planned deletions.
- Type yes when prompted to confirm.

> 🧹 This will delete Lambda functions, SNS topics, IAM roles, and any other infrastructure created by this project.

## Cost Considerations

This solution leverages mostly free-tier-eligible AWS services, but here’s a breakdown of potential costs:

- **AWS GuardDuty**
  - **Free Tier**: 30-day free trial.
  - **After Trial**: Charges based on the volume of logs analyzed and number of findings.

- **AWS Lambda**
  - **Free Tier**: 1 million requests and 400,000 GB-seconds per month.
  - **After Free Tier**: Minimal cost unless handling a high volume of events.

- **Amazon SNS**
  - **Email Notifications**: Generally low cost; subject to regional pricing and usage volume.

- **Slack**
  - **Free Plan**: Slack bots and basic integrations are supported.
  - **Paid Plans**: May be required for advanced audit logs or increased retention limits.

- **Amazon EventBridge**
  - **Pricing**: Based on number of events processed per month.

> 💰 Always monitor your AWS billing dashboard to track usage and avoid unexpected charges, especially in production environments.

## Conclusion

This project demonstrates a robust, scalable, and cost-effective solution for real-time threat detection and response using AWS services. By combining:

- **AWS GuardDuty** for continuous threat monitoring,
- **EventBridge** for real-time event routing,
- **Lambda** for enrichment and remediation logic,
- **Slack** for immediate visibility and interactive response,

you create a modern cloud-native security workflow.

Key benefits include:

- 🔐 Rapid response to EC2-based threats
- 📬 Multichannel alerting (Slack + SNS/email)
- 🧠 Context-rich notifications with instance metadata
- 🛠 Infrastructure-as-code deployment with Terraform

This setup is a strong foundation for more advanced security automation and can be extended to integrate with forensic tools, centralized logging platforms, or cross-account security controls.

## References

- [AWS GuardDuty Documentation](https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [Amazon SNS Documentation](https://docs.aws.amazon.com/sns/latest/dg/welcome.html)
- [Amazon EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html)
- [Slack API Documentation](https://api.slack.com/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions, issues, or contributions, feel free to reach out:

📧 [rbarvind04@gmail.com](mailto:rbarvind04@gmail.com)

> **Disclaimer**: Ensure you have the appropriate permissions and have reviewed AWS’s best practices and compliance requirements before deploying this solution in a production environment.
