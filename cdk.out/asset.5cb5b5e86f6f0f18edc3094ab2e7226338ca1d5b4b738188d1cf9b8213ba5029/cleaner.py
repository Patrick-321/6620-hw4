import boto3
import os

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')
    
    # List objects in the bucket
    response = s3.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        # Find the largest object
        largest_object = max(response["Contents"], key=lambda x: x["Size"])
        largest_key = largest_object["Key"]
        
        # Delete the largest object
        s3.delete_object(Bucket=bucket_name, Key=largest_key)
        print(f"Deleted largest object: {largest_key} of size {largest_object['Size']} bytes")
