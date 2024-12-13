import boto3
import os

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')
    
    # List objects in the bucket
    response = s3.list_objects_v2(Bucket=bucket_name)
    
    if "Contents" not in response:
        print("No objects found to delete.")
        return
    
    # Find the largest object
    largest_object = max(response["Contents"], key=lambda x: x["Size"])
    largest_key = largest_object["Key"]
    largest_size = largest_object["Size"]
    
    # Debugging information
    print(f"Largest object found: {largest_key} with size {largest_size} bytes")
    
    # Delete the largest object
    s3.delete_object(Bucket=bucket_name, Key=largest_key)
    print(f"Deleted largest object: {largest_key} of size {largest_size} bytes")

    return {
        'statusCode': 200,
        'body': f"Deleted the largest object: {largest_key} with size {largest_size} bytes."
    }
