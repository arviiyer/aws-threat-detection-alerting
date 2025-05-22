import json
import os
import boto3
import hmac
import hashlib
import base64
import time
import requests
from urllib.parse import parse_qs

ec2 = boto3.client("ec2")
SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']
QUARANTINE_SG_ID = os.environ['QUARANTINE_SG_ID']

def verify_slack_request(headers, sig_body):
    # Use case-insensitive lookup for Slack headers
    timestamp = next((v for k, v in headers.items() if k.lower() == "x-slack-request-timestamp"), None)
    signature = next((v for k, v in headers.items() if k.lower() == "x-slack-signature"), None)

    if not timestamp or not signature:
        return False

    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False  # Replay attack window exceeded

    sig_basestring = f"v0:{timestamp}:{sig_body.decode() if isinstance(sig_body, bytes) else sig_body}".encode()
    my_signature = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode("utf-8"),
        sig_basestring,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(my_signature, signature)

def lambda_handler(event, context):
    headers = event.get("headers", {})
    raw_body = event["body"]

    if event.get("isBase64Encoded", False):
        sig_body = base64.b64decode(raw_body)
        raw_body = sig_body.decode("utf-8")
    else:
        sig_body = raw_body.encode("utf-8")

    if not verify_slack_request(headers, sig_body):
        return {"statusCode": 401, "body": "Unauthorized Slack request"}

    payload = parse_qs(raw_body)
    if "payload" not in payload:
        return {"statusCode": 400, "body": "Missing payload from Slack"}

    try:
        action_payload = json.loads(payload["payload"][0])
        instance_id = action_payload["actions"][0]["value"]

        if instance_id == "no-instance":
            return {"statusCode": 400, "body": "No EC2 instance to quarantine"}

        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            Groups=[QUARANTINE_SG_ID]
        )

        response_url = action_payload.get("response_url")
        if response_url:
            message = {
                "text": f"✅ EC2 instance `{instance_id}` has been successfully quarantined.",
                "response_type": "ephemeral"
            }
            try:
                requests.post(response_url, json=message)
            except Exception as e:
                print("Failed to send Slack confirmation:", str(e))

        return {
            "statusCode": 200,
            "body": f"EC2 instance {instance_id} quarantined successfully"
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Failed to quarantine instance: {str(e)}"
        }

