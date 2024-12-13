import json
import boto3
import os

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')
    
    for record in event['Records']:
        message_body = json.loads(record['body'])
        sns_message = json.loads(message_body['Message'])
        
        # Extract S3 event details
        s3_event = sns_message['Records'][0]
        bucket_name = s3_event['s3']['bucket']['name']
        object_key = s3_event['s3']['object']['key']
        event_type = s3_event['eventName']
        
        # Determine size_delta based on event type
        size_delta = 0
        if event_type.startswith("ObjectCreated"):
            size_delta = s3_event['s3']['object']['size']
        elif event_type.startswith("ObjectRemoved"):
            size_delta = -s3_event['s3']['object']['size']
        
        # Log the information
        log_data = {
            "object_name": object_key,
            "size_delta": size_delta
        }
        print(json.dumps(log_data))