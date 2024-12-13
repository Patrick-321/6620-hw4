import boto3
import os
import matplotlib.pyplot as plt
import io
import time
import datetime
import matplotlib.dates as mdates

# Set MPLCONFIGDIR to /tmp to avoid matplotlib cache issues in Lambda
os.environ['MPLCONFIGDIR'] = '/tmp'

# Initialize AWS resources and environment variables
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
table_name = os.getenv('DYNAMODB_TABLE_NAME')
bucket_name = os.getenv('BUCKET_NAME')

def query_size_history():
    table = dynamodb.Table(table_name)
    now = int(time.time())
    ten_seconds_ago = now - 10

    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('BucketName').eq(bucket_name) & 
                               boto3.dynamodb.conditions.Key('Timestamp').between(ten_seconds_ago, now)
    )
    return response['Items']

def get_max_size():
    table = dynamodb.Table(table_name)
    response = table.scan(
        ProjectionExpression='TotalSize',
        FilterExpression=boto3.dynamodb.conditions.Key('BucketName').eq(bucket_name)
    )
    if not response['Items']: 
        return 0  
    
    max_size = max(int(item['TotalSize']) for item in response['Items'])
    return max_size

def plot_size_history(size_data, max_size):
    timestamps = [datetime.datetime.fromtimestamp(item['Timestamp']) for item in size_data]
    sizes = [int(item['TotalSize']) for item in size_data]
    
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, sizes, label='Bucket Size (last 10s)', marker='o')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.SecondLocator())
    plt.axhline(y=max_size, color='r', linestyle='--', label=f'Max Size: {max_size} bytes')
    plt.title('Bucket Size Changes (Last 10 Seconds)')
    plt.xlabel('Time')
    plt.ylabel('Size (Bytes)')
    plt.legend()
    plt.gcf().autofmt_xdate()

    # Save plot to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    return buf

def upload_plot_to_s3(buf):
    plot_key = 'plot.png'
    s3_client.put_object(Bucket=bucket_name, Key=plot_key, Body=buf, ContentType='image/png')

def lambda_handler(event, context):
    size_data = query_size_history()
    max_size = get_max_size()
    
    plot_buffer = plot_size_history(size_data, max_size)
    upload_plot_to_s3(plot_buffer)
    
    return {
        'statusCode': 200,
        'body': f"Plot successfully generated and uploaded to S3 as plot.png."
    }
