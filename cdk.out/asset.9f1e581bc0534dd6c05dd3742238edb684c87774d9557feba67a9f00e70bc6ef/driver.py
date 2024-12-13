import boto3
import time
import urllib3
import os

def lambda_handler(event, context):
    # Initialize boto3 clients
    s3_client = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')
    api_url = os.getenv('PLOTTING_API_URL')

    # Debugging information
    print(f"BUCKET_NAME: {bucket_name}")
    print(f"PLOTTING_API_URL: {api_url}")

    def create_object(object_name, content):
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=content)
        print(f"Object '{object_name}' created with content: {content}")

    def call_plotting_api():
        if not api_url:
            print("Error: PLOTTING_API_URL is not set.")
            return

        http = urllib3.PoolManager()
        response = http.request('POST', api_url)
        print("Plotting API invoked:", response.status)

    # Operations as per requirements
    # Step 1: Create assignment1.txt (19 bytes)
    create_object('assignment1.txt', 'Empty Assignment 1')
    time.sleep(3)  # Wait to allow the metric to update and potentially trigger an alarm

    # Step 2: Create assignment2.txt (28 bytes)
    create_object('assignment2.txt', 'Empty Assignment 2222222222')
    time.sleep(3)  # Wait for alarm and Cleaner Lambda to delete assignment2.txt

    # Step 3: Create assignment3.txt (2 bytes)
    create_object('assignment3.txt', '33')
    time.sleep(20)  # Wait for alarm and Cleaner Lambda to delete assignment1.txt

    # Step 4: Call the plotting API
    call_plotting_api()

    return {
        'statusCode': 200,
        'body': 'Driver Lambda executed successfully and invoked Plotting API.'
    }
