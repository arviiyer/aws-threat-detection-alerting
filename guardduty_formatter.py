import json
import os
import boto3
import requests

sns_client = boto3.client('sns')
ec2_client = boto3.client('ec2')

sns_topic_arn = os.environ['SNS_TOPIC_ARN']
slack_token = os.environ['SLACK_BOT_TOKEN']
slack_channel = "#alert-notifications"

def lambda_handler(event, context):
    # Parse the GuardDuty finding
    detail = event.get('detail', {})
    finding_type = detail.get('type', 'Unknown')
    severity = detail.get('severity', 'Unknown')
    description = detail.get('description', 'No description provided')
    region = detail.get('region', 'Unknown')
    account = detail.get('accountId', 'Unknown')
    time = detail.get('updatedAt', 'Unknown')
    title = detail.get('title', 'GuardDuty Finding')
    finding_id = detail.get('id', 'N/A')

    # Try to extract EC2 instance ID
    resource = detail.get("resource", {})
    instance_id = (
        resource.get("instanceDetails", {}).get("instanceId") or
        resource.get("instanceId")
    )

    ec2_enrichment_text = ""
    if instance_id:
        try:
            ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = ec2_response['Reservations'][0]['Instances'][0]

            instance_type = instance.get('InstanceType', 'Unknown')
            launch_time = str(instance.get('LaunchTime', 'Unknown'))
            private_ip = instance.get('PrivateIpAddress', 'Unknown')
            public_ip = instance.get('PublicIpAddress', 'N/A')
            vpc_id = instance.get('VpcId', 'Unknown')
            subnet_id = instance.get('SubnetId', 'Unknown')
            tags = instance.get('Tags', [])
            tag_dict = {tag['Key']: tag['Value'] for tag in tags}
            name = tag_dict.get("Name", "N/A")
            owner = tag_dict.get("Owner", "N/A")
            environment = tag_dict.get("Environment", "N/A")

            ec2_enrichment_text = f"""
EC2 Enrichment:
- Instance ID: {instance_id}
- Name: {name}
- Owner: {owner}
- Environment: {environment}
- Type: {instance_type}
- Private IP: {private_ip}
- Public IP: {public_ip}
- VPC: {vpc_id}
- Subnet: {subnet_id}
- Launch Time: {launch_time}
            """.strip()
        except Exception as e:
            ec2_enrichment_text = f"(Failed to enrich EC2 info: {e})"

    def sanitize_subject(text):
        sanitized_text = text.encode('ascii', 'ignore').decode('ascii')
        max_subject_length = 100
        subject_prefix = "GuardDuty Alert: "
        max_title_length = max_subject_length - len(subject_prefix)
        return sanitized_text[:max_title_length]

    sanitized_title = sanitize_subject(title)
    subject = f"GuardDuty Alert: {sanitized_title}"

    console_link = f"https://{region}.console.aws.amazon.com/guardduty/home?region={region}#/findings?macros=current&fId={finding_id}"

    message = f"""
GuardDuty Finding Alert

Title: {title}
Type: {finding_type}
Severity: {severity}
Account ID: {account}
Region: {region}
Time: {time}

Description:
{description}

{ec2_enrichment_text}

Recommendation:
Please review the finding in the AWS GuardDuty console and take appropriate action.

Link to Finding:
{console_link}
    """.strip()

    # Publish to SNS
    sns_client.publish(
        TopicArn=sns_topic_arn,
        Subject=subject,
        Message=message
    )

    # Send to Slack
    slack_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {slack_token}"
    }

    slack_payload = {
        "channel": slack_channel,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{subject}*\n*Severity:* {severity}\n*Region:* {region}\n*Type:* {finding_type}\n*Description:* {description}\n\n{ec2_enrichment_text}\n\n<{console_link}|View in Console>"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🛑 Quarantine EC2"
                        },
                        "style": "danger",
                        "value": instance_id if instance_id else "no-instance",
                        "action_id": "quarantine_instance"
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post("https://slack.com/api/chat.postMessage", headers=slack_headers, json=slack_payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Slack notification failed: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps('Notification sent to SNS and Slack')
    }

