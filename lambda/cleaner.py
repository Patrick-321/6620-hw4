import boto3
import os

def lambda_handler(event, context):
    # Initialize S3 client
    s3_client = boto3.client('s3')
    target_bucket = os.getenv('BUCKET_NAME')
    print(f"Target bucket: {target_bucket}")
    
    # Retrieve the list of objects in the specified bucket
    response = s3_client.list_objects_v2(Bucket=target_bucket)
    if "Contents" in response:
        # Identify the largest file based on its size
        largest_file = max(response["Contents"], key=lambda obj: obj["Size"])
        largest_file_key = largest_file["Key"]
        
        # Log details of the largest file
        print(f"Largest file identified: {largest_file_key} ({largest_file['Size']} bytes)")
        
        # Remove the largest file from the bucket
        s3_client.delete_object(Bucket=target_bucket, Key=largest_file_key)
        print(f"Successfully deleted: {largest_file_key} ({largest_file['Size']} bytes)")
    else:
        print("The bucket does not contain any files to delete.")
