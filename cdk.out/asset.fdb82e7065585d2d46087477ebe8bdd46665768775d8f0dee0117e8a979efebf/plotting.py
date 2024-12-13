import boto3
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
table_name = os.getenv('DYNAMODB_TABLE_NAME')
bucket_name = os.getenv('BUCKET_NAME')
plot_bucket = os.getenv('PLOT_BUCKET_NAME')

def query_size_history():
    table = dynamodb.Table(table_name)
    now = datetime.utcnow()
    ten_seconds_ago = int((now - timedelta(seconds=10)).timestamp())
    
    # Continuously query the last 10 seconds of data
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('BucketName').eq(bucket_name) & 
        boto3.dynamodb.conditions.Key('Timestamp').between(ten_seconds_ago, int(now.timestamp()))
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
    
    max_size = max(item['TotalSize'] for item in response['Items'])
    return max_size

def plot_size_history(size_data, max_size):
    timestamps = [item['TimestampStr'] for item in size_data]
    sizes = [item['TotalSize'] for item in size_data]
    
    plt.figure()
    plt.plot(timestamps, sizes, label='Bucket Size')
    plt.axhline(y=max_size, color='r', linestyle='--', label='Max Size')
    plt.xlabel('Timestamp')
    plt.ylabel('Size (Bytes)')
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.tight_layout()       # Adjust layout to prevent label cutoff
    plt.legend()
    
    plt.savefig('/tmp/plot.png') 

def upload_plot_to_s3():
    with open('/tmp/plot.png', 'rb') as f:
        s3_client.put_object(Bucket=plot_bucket, Key='plot.png', Body=f)

def lambda_handler(event, context):
    size_data = query_size_history()
    max_size = get_max_size()
    
    plot_size_history(size_data, max_size)
    upload_plot_to_s3()
    
    return {
        'statusCode': 200,
        'body': 'Plotting Lambda executed successfully, plot uploaded to S3.'
    }

