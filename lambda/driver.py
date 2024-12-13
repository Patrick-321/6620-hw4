import boto3
import time
import urllib3
import os

def lambda_handler(event, context):
    # Set up boto3 client for S3 and retrieve environment variables
    s3 = boto3.client('s3')
    bucket = os.getenv('BUCKET_NAME')
    plotting_api = os.getenv('PLOTTING_API_URL')

    # Logging details for debugging purposes
    print(f"Bucket Name: {bucket}")
    print(f"Plotting API URL: {plotting_api}")

    def upload_file(file_name, file_content):
        s3.put_object(Bucket=bucket, Key=file_name, Body=file_content)
        print(f"File '{file_name}' uploaded with content: {file_content}")

    def invoke_plotting_service():
        if not plotting_api:
            print("Error: Plotting API URL is not defined.")
            return

        http_manager = urllib3.PoolManager()
        response = http_manager.request('POST', plotting_api)
        print("Plotting service triggered, response status:", response.status)

    # Execute required operations
    # Step 1: Upload 'assignment1.txt' (19 bytes)
    upload_file('assignment1.txt', 'Empty Assignment 1')
    time.sleep(3)  # Pause to allow metrics updates and alarms if applicable

    # Step 2: Upload 'assignment2.txt' (28 bytes)
    upload_file('assignment2.txt', 'Empty Assignment 2')
    time.sleep(3)  # Pause to account for alarm processing and cleanup actions

    # Step 3: Upload 'assignment3.txt' (2 bytes)
    upload_file('assignment3.txt', '3')
    time.sleep(3)  # Pause for potential alarm processing and cleanup actions

    # Step 4: Invoke the plotting service
    invoke_plotting_service()

    return {
        'statusCode': 200,
        'body': 'Driver Lambda executed successfully and plotting service invoked.'
    }
