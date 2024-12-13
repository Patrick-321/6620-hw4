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
            # For ObjectCreated events, retrieve size if available
            size_delta = s3_event['s3']['object'].get('size', 0)
        elif event_type.startswith("ObjectRemoved"):
            # For ObjectRemoved events, retrieve size by making a head_object call
            try:
                head_response = s3.head_object(Bucket=bucket_name, Key=object_key)
                size_delta = -head_response['ContentLength']
            except s3.exceptions.ClientError as e:
                print(f"Error retrieving object size for deleted object {object_key}: {e}")
                size_delta = 0  # Default to 0 if object size cannot be retrieved
        
        # Log the information
        log_data = {
            "object_name": object_key,
            "size_delta": size_delta
        }
        print(json.dumps(log_data))
