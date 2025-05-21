import json
import os
import boto3
import requests

sns_client = boto3.client('sns')
sns_topic_arn = os.environ['SNS_TOPIC_ARN']
slack_token = os.environ['SLACK_BOT_TOKEN']
slack_channel = "#alert-notifications"  # <-- change this to your actual Slack channel

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

    # Sanitize the title
    def sanitize_subject(text):
        sanitized_text = text.encode('ascii', 'ignore').decode('ascii')
        max_subject_length = 100
        subject_prefix = "GuardDuty Alert: "
        max_title_length = max_subject_length - len(subject_prefix)
        return sanitized_text[:max_title_length]

    sanitized_title = sanitize_subject(title)
    subject = f"GuardDuty Alert: {sanitized_title}"

    # Format shared message
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

    Recommendation:
    Please review the finding in the AWS GuardDuty console and take appropriate action.

    Link to Finding:
    {console_link}
    """

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
        "text": f"*{subject}*\n*Severity:* {severity}\n*Region:* {region}\n*Type:* {finding_type}\n*Description:* {description}\n<{console_link}|View in Console>"
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

