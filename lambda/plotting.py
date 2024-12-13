import boto3
import os
import matplotlib.pyplot as plt
import io
import time
import datetime
import matplotlib.dates as mdates

# Configure MPLCONFIGDIR to use /tmp for Matplotlib in AWS Lambda
os.environ['MPLCONFIGDIR'] = '/tmp'

# Initialize AWS clients and environment variables
dynamodb_resource = boto3.resource('dynamodb')
s3 = boto3.client('s3')
dynamodb_table_name = os.getenv('DYNAMODB_TABLE_NAME')
source_bucket = os.getenv('BUCKET_NAME')
plotting_bucket = os.getenv('PLOT_BUCKET_NAME')

def fetch_size_history():
    table = dynamodb_resource.Table(dynamodb_table_name)
    current_time = int(time.time())
    ten_seconds_prior = current_time - 10
    print(type(current_time), type(ten_seconds_prior))
    print(type(source_bucket))
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('BucketName').eq(source_bucket) &
                               boto3.dynamodb.conditions.Key('Timestamp').between(ten_seconds_prior, current_time)
    )
    return response['Items']

def retrieve_max_size():
    table = dynamodb_resource.Table(dynamodb_table_name)
    response = table.scan(
        ProjectionExpression='TotalSize',
        FilterExpression=boto3.dynamodb.conditions.Key('BucketName').eq(source_bucket)
    )
    if not response['Items']:
        return 0

    largest_size = max(int(item['TotalSize']) for item in response['Items'])
    return largest_size

def generate_size_plot(size_history, max_bucket_size):
    timestamps = [datetime.datetime.fromtimestamp(item['Timestamp']) for item in size_history]
    sizes = [int(item['TotalSize']) for item in size_history]
    
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, sizes, label='Bucket Size (Last 10 Seconds)', marker='o')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.SecondLocator())
    plt.axhline(y=max_bucket_size, color='r', linestyle='--', label=f'Max Size: {max_bucket_size} bytes')
    plt.title('Changes in Bucket Size (Last 10 Seconds)')
    plt.xlabel('Time')
    plt.ylabel('Size (Bytes)')
    plt.legend()
    plt.gcf().autofmt_xdate()

    # Save the plot into a memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    return buffer

def upload_plot(buffer):
    plot_filename = 'plot.png'
    s3.put_object(Bucket=plotting_bucket, Key=plot_filename, Body=buffer, ContentType='image/png')

def lambda_handler(event, context):
    size_history = fetch_size_history()
    max_bucket_size = retrieve_max_size()
    
    plot_buffer = generate_size_plot(size_history, max_bucket_size)
    upload_plot(plot_buffer)
    
    return {
        'statusCode': 200,
        'body': "Plot successfully created and uploaded to S3 as plot.png."
    }
