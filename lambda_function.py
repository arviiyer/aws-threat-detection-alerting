import json
import os
import boto3

sns_client = boto3.client('sns')
sns_topic_arn = os.environ['SNS_TOPIC_ARN']

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

    # Format the message
    message = f"""
    **GuardDuty Finding Alert**

    **Title:** {title}
    **Type:** {finding_type}
    **Severity:** {severity}
    **Account ID:** {account}
    **Region:** {region}
    **Time:** {time}

    **Description:**
    {description}

    **Recommendation:**
    Please review the finding in the AWS GuardDuty console and take appropriate action.

    **Link to Finding:**
    https://{region}.console.aws.amazon.com/guardduty/home?region={region}#/findings?macros=current&fId={detail.get('id', '')}
    """

    # Publish the message to SNS
    response = sns_client.publish(
        TopicArn=sns_topic_arn,
        Subject=f"GuardDuty Alert: {title}",
        Message=message
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Notification sent')
    }
