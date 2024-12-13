import boto3
import os
import time

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')
    print(f"Bucket name: {bucket_name}")   
    
    # Repeat deletion until bucket size is below the threshold
    while True:
        # List objects in the bucket
        response = s3.list_objects_v2(Bucket=bucket_name)
        
        if "Contents" not in response:
            print("No objects found to delete.")
            break
        
        # Find the largest object
        largest_object = max(response["Contents"], key=lambda x: x["Size"])
        largest_key = largest_object["Key"]
        largest_size = largest_object["Size"]
        
        # Debugging information
        print(f"Largest object found: {largest_key} with size {largest_size} bytes")
        
        # Delete the largest object
        s3.delete_object(Bucket=bucket_name, Key=largest_key)
        print(f"Deleted largest object: {largest_key} of size {largest_size} bytes")
        
        # Wait a moment to let CloudWatch update the metric
        time.sleep(2)
        
        # Exit if we assume the alarm would be reset
        if largest_size < 20:
            print("Assuming bucket size is below threshold, stopping deletion.")
            break
