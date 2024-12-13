import boto3
from datetime import datetime
import os

# Initialize AWS clients and environment variables
s3 = boto3.client('s3')
dynamodb_resource = boto3.resource('dynamodb')
source_bucket = os.environ['BUCKET_NAME']
dynamodb_table = os.environ['DYNAMODB_TABLE_NAME']

def compute_bucket_metrics():
    # Fetch the list of objects in the bucket
    response = s3.list_objects_v2(Bucket=source_bucket)
    total_bucket_size = 0
    total_objects = 0
    
    if 'Contents' in response:
        # Compute the total size and count the objects in the bucket
        for item in response['Contents']:
            total_bucket_size += item['Size']
            total_objects += 1
    
    return total_bucket_size, total_objects

def log_metrics_to_dynamodb(total_size, object_count):
    table = dynamodb_resource.Table(dynamodb_table)
    current_timestamp = int(datetime.utcnow().timestamp())
    formatted_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Store metrics in DynamoDB
    table.put_item(
        Item={
            'BucketName': source_bucket,
            'Timestamp': current_timestamp,
            'TimestampStr': formatted_timestamp,
            'TotalSize': total_size,
            'ObjectCount': object_count
        }
    )

def lambda_handler(event, context):
    # Calculate bucket metrics (size and object count)
    bucket_size, object_count = compute_bucket_metrics()

    # Log metrics into DynamoDB
    log_metrics_to_dynamodb(bucket_size, object_count)

    return {
        'statusCode': 200,
        'body': 'Metrics logging Lambda executed successfully.'
    }
