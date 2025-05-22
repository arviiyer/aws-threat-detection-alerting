import json
import os
import boto3
import hmac
import hashlib
import base64
from urllib.parse import parse_qs

ec2 = boto3.client("ec2")
SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']
QUARANTINE_SG_ID = os.environ['QUARANTINE_SG_ID']

def verify_slack_request(headers, body):
    timestamp = headers.get("X-Slack-Request-Timestamp")
    signature = headers.get("X-Slack-Signature")

    if not timestamp or not signature:
        return False

    sig_basestring = f"v0:{timestamp}:{body}".encode("utf-8")
    my_signature = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode("utf-8"),
        sig_basestring,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(my_signature, signature)

def lambda_handler(event, context):
    headers = event.get("headers", {})
    body = event.get("body", "")

    if not verify_slack_request(headers, body):
        return {"statusCode": 401, "body": "Unauthorized Slack request"}

    payload = parse_qs(body)
    action_payload = json.loads(payload.get("payload")[0])
    instance_id = action_payload["actions"][0]["value"]

    if instance_id == "no-instance":
        return {"statusCode": 400, "body": "No EC2 instance to quarantine"}

    try:
        # Quarantine instance by setting SG
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            Groups=[QUARANTINE_SG_ID]
        )
        return {
            "statusCode": 200,
            "body": f"EC2 instance {instance_id} quarantined successfully"
        }
    except Exception as e:
        print(f"Error quarantining instance: {e}")
        return {
            "statusCode": 500,
            "body": f"Failed to quarantine instance {instance_id}: {str(e)}"
        }

