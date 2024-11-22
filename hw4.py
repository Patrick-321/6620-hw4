# driver

import boto3
import time
import urllib3
import os

def lambda_handler(event, context):
    """
    AWS Lambda function for interacting with S3 and invoking a plotting API.

    - Creates, updates, and deletes objects in an S3 bucket.
    - Invokes a plotting API via an HTTP POST request.

    Parameters:
        event (dict): Event data (not used in this function).
        context (object): Lambda context object (not used in this function).

    Returns:
        dict: Response indicating the status of the Lambda execution.
    """
    # Initialize boto3 clients
    s3_client = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')
    api_url = os.getenv('PLOTTING_API_URL')

    # Debugging information
    print(f"BUCKET_NAME: {bucket_name}")
    print(f"PLOTTING_API_URL: {api_url}")

    def create_object(object_name, content):
        """
        Create an object in the specified S3 bucket.

        Parameters:
            object_name (str): Name of the object to create.
            content (str): Content of the object.
        """
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=content)
        print(f"Object '{object_name}' created with content: {content}")

    def update_object(object_name, content):
        """
        Update an object in the specified S3 bucket.

        Parameters:
            object_name (str): Name of the object to update.
            content (str): New content of the object.
        """
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=content)
        print(f"Object '{object_name}' updated with content: {content}")

    def delete_object(object_name):
        """
        Delete an object from the specified S3 bucket.

        Parameters:
            object_name (str): Name of the object to delete.
        """
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        print(f"Object '{object_name}' deleted.")

    def call_plotting_api():
        """
        Invoke the plotting API using an HTTP POST request.
        """
        if not api_url:
            print("Error: PLOTTING_API_URL is not set.")
            return

        http = urllib3.PoolManager()
        response = http.request('POST', api_url)
        print(f"Plotting API invoked with status: {response.status}")

    # Operations
    create_object('assignment1.txt', 'Empty Assignment 1')
    time.sleep(2)

    update_object('assignment1.txt', 'Empty Assignment 2')
    time.sleep(2)

    delete_object('assignment1.txt')
    time.sleep(2)

    create_object('assignment2.txt', '21')
    time.sleep(2)

    call_plotting_api()

    return {
        'statusCode': 200,
        'body': 'Driver Lambda executed successfully and invoked Plotting API.'
    }


# plotting
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
table_name = os.getenv('DYNAMODB_TABLE_NAME')
s3_client = boto3.client('s3')
bucket_name = os.getenv('BUCKET_NAME')

def query_size_history():
    """
    Query the DynamoDB table for bucket size data over the last 10 seconds.

    Returns:
        list: List of items containing size history data.
    """
    table = dynamodb.Table(table_name)
    now = int(time.time())
    ten_seconds_ago = now - 10

    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('BucketName').eq(bucket_name) &
                               boto3.dynamodb.conditions.Key('Timestamp').between(ten_seconds_ago, now)
    )
    return response['Items']

def get_max_size():
    """
    Retrieve the maximum bucket size from DynamoDB.

    Returns:
        int: The maximum size of the bucket, or 0 if no data exists.
    """
    table = dynamodb.Table(table_name)
    response = table.scan(
        ProjectionExpression='TotalSize',
        FilterExpression=boto3.dynamodb.conditions.Key('BucketName').eq(bucket_name)
    )

    if not response['Items']:
        return 0

    return max(int(item['TotalSize']) for item in response['Items'])

def plot_size_history(size_data, max_size):
    """
    Generate a plot of bucket size history and maximum size.

    Parameters:
        size_data (list): List of size history data from DynamoDB.
        max_size (int): The maximum bucket size.

    Returns:
        io.BytesIO: Buffer containing the generated plot image.
    """
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
    """
    Upload the plot image to an S3 bucket.

    Parameters:
        buf (io.BytesIO): Buffer containing the plot image.
    """
    plot_key = 'plot.png'
    s3_client.put_object(Bucket=bucket_name, Key=plot_key, Body=buf, ContentType='image/png')

def lambda_handler(event, context):
    """
    AWS Lambda function handler for plotting and uploading bucket size history.

    Parameters:
        event (dict): Event data (not used in this function).
        context (object): Lambda context object (not used in this function).

    Returns:
        dict: Response indicating the status of the Lambda execution.
    """
    size_data = query_size_history()
    max_size = get_max_size()

    plot_buffer = plot_size_history(size_data, max_size)
    upload_plot_to_s3(plot_buffer)

    return {
        'statusCode': 200,
        'body': 'Plot successfully generated and uploaded to S3 as plot.png.'
    }



# size
from aws_cdk import Stack, Duration
from aws_cdk.aws_s3 import Bucket, EventType
from aws_cdk.aws_s3_notifications import LambdaDestination
from aws_cdk.aws_dynamodb import Table, Attribute, AttributeType, BillingMode
from aws_cdk.aws_lambda import Function, Runtime, Code
from constructs import Construct

class SizeTrackingLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        """
        Stack to set up an S3 bucket with event notifications, a DynamoDB table for tracking,
        and a Lambda function to monitor bucket size changes.

        Parameters:
            scope (Construct): The scope within which this construct is defined.
            id (str): The unique identifier for the stack.
            kwargs: Additional keyword arguments.
        """
        super().__init__(scope, id, **kwargs)

        # Create S3 Bucket
        self.bucket = Bucket(self, "Assignment3Bucket")

        # Create DynamoDB Table
        self.table = Table(
            self, "TrackingTable",
            partition_key=Attribute(name="BucketName", type=AttributeType.STRING),
            sort_key=Attribute(name="Timestamp", type=AttributeType.NUMBER),
            billing_mode=BillingMode.PAY_PER_REQUEST
        )

        # Create Size Tracking Lambda Function
        self.size_tracking_lambda = Function(
            self, "SizeTrackingLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="size.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),
            environment={
                'DYNAMODB_TABLE_NAME': self.table.table_name,
                'BUCKET_NAME': self.bucket.bucket_name
            }
        )

        # Grant Lambda permissions for S3 and DynamoDB access
        self.bucket.grant_read_write(self.size_tracking_lambda)
        self.table.grant_read_write_data(self.size_tracking_lambda)

        # Add S3 bucket event notifications
        self.bucket.add_event_notification(
            EventType.OBJECT_CREATED,
            LambdaDestination(self.size_tracking_lambda)
        )
        self.bucket.add_event_notification(
            EventType.OBJECT_REMOVED,
            LambdaDestination(self.size_tracking_lambda)
        )


# api gateway stack
from aws_cdk import Stack, CfnOutput
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration
from aws_cdk.aws_lambda import Function
from constructs import Construct

class ApiGatewayStack(Stack):
    def __init__(self, scope: Construct, id: str, plotting_lambda: Function, **kwargs):
        """
        Stack to set up an API Gateway with a Lambda integration.

        Parameters:
            scope (Construct): The scope within which this construct is defined.
            id (str): The unique identifier for the stack.
            plotting_lambda (Function): The Lambda function integrated with the API Gateway.
            kwargs: Additional keyword arguments.
        """
        super().__init__(scope, id, **kwargs)

        # Create API Gateway
        api = RestApi(
            self, "PlottingApi",
            rest_api_name="Plotting Service",
            description="API Gateway to trigger the Plotting Lambda."
        )

        # Add a resource and method to the API Gateway
        plot_resource = api.root.add_resource("plot")
        plot_integration = LambdaIntegration(plotting_lambda)
        plot_resource.add_method("POST", plot_integration)

        # Store the API URL and ID as outputs
        self.api_url = f"{api.url}plot"
        self.api_id = api.rest_api_id

        CfnOutput(self, "PlottingApiId", value=self.api_id)
        CfnOutput(self, "PlottingApiUrl", value=self.api_url)

# app entrypoint
from aws_cdk import App
from size_tracking_lambda_stack import SizeTrackingLambdaStack
from plotting_lambda_stack import PlottingLambdaStack
from api_stack import ApiGatewayStack
from driver_lambda_stack import DriverLambdaStack

# Initialize the CDK application
app = App()

# Create SizeTrackingLambdaStack to set up S3 and DynamoDB resources along with Size Tracking Lambda
size_tracking_lambda_stack = SizeTrackingLambdaStack(app, "SizeTrackingStack")

# Create PlottingLambdaStack to set up the Plotting Lambda function
plotting_lambda_stack = PlottingLambdaStack(
    app, "PlottingLambdaStack",
    dynamodb_table=size_tracking_lambda_stack.table,
    s3_bucket=size_tracking_lambda_stack.bucket
)

# Create ApiGatewayStack to integrate with the Plotting Lambda function
api_gateway_stack = ApiGatewayStack(
    app, "ApiGatewayStack",
    plotting_lambda=plotting_lambda_stack.plotting_lambda
)

# Create DriverLambdaStack to pass in the API URL and API ID for invocation
driver_lambda_stack = DriverLambdaStack(
    app, "DriverLambdaStack",
    s3_bucket=size_tracking_lambda_stack.bucket,
    plotting_api_url=api_gateway_stack.api_url,
    plotting_api_id=api_gateway_stack.api_id
)

# Synthesize the application
app.synth()



# driver lambda
from aws_cdk import Stack, Duration, Aws
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_iam import PolicyStatement
from constructs import Construct

class DriverLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, s3_bucket: Bucket, plotting_api_url: str, plotting_api_id: str, **kwargs):
        """
        Stack to create the Driver Lambda function with permissions to interact with S3 and invoke the API Gateway.

        Parameters:
            scope (Construct): The scope within which this construct is defined.
            id (str): The unique identifier for the stack.
            s3_bucket (Bucket): The S3 bucket to which the Lambda function writes.
            plotting_api_url (str): The URL of the API Gateway.
            plotting_api_id (str): The ID of the API Gateway.
            kwargs: Additional keyword arguments.
        """
        super().__init__(scope, id, **kwargs)

        # Define the Driver Lambda function
        self.driver_lambda = Function(
            self, "DriverLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="driver.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),
            environment={
                'BUCKET_NAME': s3_bucket.bucket_name,
                'PLOTTING_API_URL': plotting_api_url
            }
        )

        # Grant write permissions to the S3 bucket
        s3_bucket.grant_write(self.driver_lambda)

        # Grant permission for the Lambda to invoke the API Gateway
        self.driver_lambda.add_to_role_policy(PolicyStatement(
            actions=["execute-api:Invoke"],
            resources=[
                f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{plotting_api_id}/prod/*"
            ]
        ))


# plotting lambda stack
from aws_cdk import Stack, Duration
from aws_cdk.aws_lambda import Function, Runtime, Code, Architecture, LayerVersion
from aws_cdk.aws_dynamodb import Table
from aws_cdk.aws_s3 import Bucket
from constructs import Construct

class PlottingLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, dynamodb_table: Table, s3_bucket: Bucket, **kwargs):
        """
        Stack to create the Plotting Lambda function with necessary resources and permissions.

        Parameters:
            scope (Construct): The scope within which this construct is defined.
            id (str): The unique identifier for the stack.
            dynamodb_table (Table): The DynamoDB table for data access.
            s3_bucket (Bucket): The S3 bucket for storing plot outputs.
            kwargs: Additional keyword arguments.
        """
        super().__init__(scope, id, **kwargs)

        # Define the Matplotlib Layer ARN
        layer_arn = "arn:aws:lambda:us-west-1:188366678271:layer:matplot:4"
        matplotlib_layer = LayerVersion.from_layer_version_arn(self, "MatplotlibLayer", layer_arn)

        # Define the Plotting Lambda function
        self.plotting_lambda = Function(
            self, "PlottingLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="plotting.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),
            architecture=Architecture.ARM_64,
            layers=[matplotlib_layer],
            environment={
                'DYNAMODB_TABLE_NAME': dynamodb_table.table_name,
                'BUCKET_NAME': s3_bucket.bucket_name
            }
        )

        # Grant permissions to the Lambda function for S3 and DynamoDB access
        s3_bucket.grant_read_write(self.plotting_lambda)
        dynamodb_table.grant_read_write_data(self.plotting_lambda)


# size tracking lambda stack
from aws_cdk import Stack, Duration
from aws_cdk.aws_s3 import Bucket, EventType
from aws_cdk.aws_s3_notifications import LambdaDestination
from aws_cdk.aws_dynamodb import Table, Attribute, AttributeType, BillingMode
from aws_cdk.aws_lambda import Function, Runtime, Code
from constructs import Construct

class SizeTrackingLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        """
        Stack to set up an S3 bucket, DynamoDB table, and Size Tracking Lambda function.

        Parameters:
            scope (Construct): The scope within which this construct is defined.
            id (str): The unique identifier for the stack.
            kwargs: Additional keyword arguments.
        """
        super().__init__(scope, id, **kwargs)

        # Create S3 Bucket
        self.bucket = Bucket(self, "Assignment3Bucket")

        # Create DynamoDB Table
        self.table = Table(
            self, "TrackingTable",
            partition_key=Attribute(name="BucketName", type=AttributeType.STRING),
            sort_key=Attribute(name="Timestamp", type=AttributeType.NUMBER),
            billing_mode=BillingMode.PAY_PER_REQUEST
        )

        # Create Size Tracking Lambda Function
        self.size_tracking_lambda = Function(
            self, "SizeTrackingLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="size.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),
            environment={
                'DYNAMODB_TABLE_NAME': self.table.table_name,
                'BUCKET_NAME': self.bucket.bucket_name
            }
        )

        # Grant permissions for S3 and DynamoDB access
        self.bucket.grant_read_write(self.size_tracking_lambda)
        self.table.grant_read_write_data(self.size_tracking_lambda)

        # Add S3 bucket event notifications to trigger the Lambda function
        self.bucket.add_event_notification(
            EventType.OBJECT_CREATED,
            LambdaDestination(self.size_tracking_lambda)
        )
        self.bucket.add_event_notification(
            EventType.OBJECT_REMOVED,
            LambdaDestination(self.size_tracking_lambda)
        )

