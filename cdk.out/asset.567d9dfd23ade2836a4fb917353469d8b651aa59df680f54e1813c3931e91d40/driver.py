import boto3
import time
import urllib3
import os

# Initialize boto3 clients
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

bucket_name = os.getenv('BUCKET_NAME')
api_url = os.getenv('PLOTTING_API_URL')

def create_object(object_name, content):
    s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=content)
    print(f"Object '{object_name}' created with content: {content}")

def update_object(object_name, content):
    s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=content)
    print(f"Object '{object_name}' updated with content: {content}")

def delete_object(object_name):
    s3_client.delete_object(Bucket=bucket_name, Key=object_name)
    print(f"Object '{object_name}' deleted.")


def call_plotting_api():
    api_url = api_url
    
    http = urllib3.PoolManager()
    response = http.request('POST', api_url)
    
    print("Plotting API invoked:", response.status)

def lambda_handler(event, context):
    create_object('assignment1.txt', 'Empty Assignment 1')
    time.sleep(2)

    update_object('assignment1.txt', 'Empty Assignment 2222222222')
    time.sleep(2)

    delete_object('assignment1.txt')
    time.sleep(2)

    create_object('assignment2.txt', '33')
    time.sleep(2)
    
    call_plotting_api()

    return {
        'statusCode': 200,
        'body': 'Driver Lambda executed successfully and invoked Plotting API.'
    }