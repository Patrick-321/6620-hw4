from aws_cdk import App
from aws_cdk.aws_s3 import Bucket
from size_tracking_lambda_stack import SizeTrackingLambdaStack
from plotting_lambda_stack import PlottingLambdaStack
from api_stack import PlotApiGatewayStack
from driver_lambda_stack import DriverLambdaStack
from storage_and_notification_stack import StorageAndNotificationStack
from logging_lambda_stack import LoggingLambdaStack
from constructs import Construct

app = App()

# Set up the storage stack to create the S3 bucket and notifications
storage_notification_stack = StorageAndNotificationStack(app, "StorageNotificationStack")

# Create the stack for size tracking, which sets up DynamoDB and the size tracking Lambda
size_tracker_stack = SizeTrackingLambdaStack(
    app, 
    "SizeTrackerStack", 
    sns_topic=storage_notification_stack.sns_topic, 
    s3_bucket=storage_notification_stack.s3_bucket
)

# Set up the plotting Lambda stack, integrating it with DynamoDB and the S3 bucket
plot_lambda_stack = PlottingLambdaStack(
    app, 
    "PlotLambdaStack",
    dynamodb_table=size_tracker_stack.table,
    s3_bucket=storage_notification_stack.s3_bucket
)

# Create the API Gateway stack and link it with the plotting Lambda
api_gateway_stack = PlotApiGatewayStack(
    app, 
    "PlotApiGatewayStack", 
    lambda_function=plot_lambda_stack.plotting_lambda
)

# Set up the driver Lambda stack, passing in the API details and S3 bucket
driver_stack = DriverLambdaStack(
    app, 
    "DriverLambdaStack",
    s3_bucket=storage_notification_stack.s3_bucket, 
    plotting_api_url=api_gateway_stack.api_url,
    plotting_api_id=api_gateway_stack.api_id
)

# Set up the logging Lambda stack, passing in the SNS topic and S3 bucket
logging_stack = LoggingLambdaStack(
    app, 
    "LoggingLambdaStack", 
    sns_topic=storage_notification_stack.sns_topic, 
    s3_bucket=storage_notification_stack.s3_bucket
)

# Synthesize the CloudFormation template
app.synth()
