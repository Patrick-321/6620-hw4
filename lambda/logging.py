import json
import boto3
import os

def lambda_handler(event, context):
    # Initialize the S3 client
    s3_client = boto3.client('s3')
    target_bucket = os.getenv('BUCKET_NAME')
    
    for record in event['Records']:
        # Parse the message body from the event
        msg_body = json.loads(record['body'])
        sns_payload = json.loads(msg_body['Message'])
        
        # Extract details from the S3 event
        s3_event_details = sns_payload['Records'][0]
        source_bucket = s3_event_details['s3']['bucket']['name']
        object_key = s3_event_details['s3']['object']['key']
        event_action = s3_event_details['eventName']
        
        # Calculate the size change based on the event type
        size_change = 0
        if event_action.startswith("ObjectCreated"):
            size_change = s3_event_details['s3']['object'].get('size', 0)  # Default to 0 if size is absent
        elif event_action.startswith("ObjectRemoved"):
            size_change = -s3_event_details['s3']['object'].get('size', 0)  # Default to 0 if size is absent
        
        # Log event details
        event_log = {
            "file_name": object_key,
            "size_change": size_change
        }
        print(json.dumps(event_log))
