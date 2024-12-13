from aws_cdk import Stack, Duration
from aws_cdk.aws_dynamodb import Table, Attribute, AttributeType, BillingMode
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from constructs import Construct
from aws_cdk.aws_sqs import Queue
from aws_cdk.aws_sns import Topic
from aws_cdk.aws_sns_subscriptions import SqsSubscription
from aws_cdk.aws_s3 import Bucket

class BucketSizeTrackerStack(Stack):
    def __init__(self, scope: Construct, stack_id: str, topic: Topic, bucket: Bucket, **kwargs):
        super().__init__(scope, stack_id, **kwargs)

        # Define a DynamoDB table for tracking bucket metrics
        tracking_table = Table(
            self, "BucketMetricsTable",
            partition_key=Attribute(name="BucketName", type=AttributeType.STRING),
            sort_key=Attribute(name="Timestamp", type=AttributeType.NUMBER),
            billing_mode=BillingMode.PAY_PER_REQUEST
        )

        # Create an SQS queue and subscribe it to the SNS topic
        event_queue = Queue(self, "BucketEventQueue", visibility_timeout=Duration.seconds(300))
        topic.add_subscription(SqsSubscription(event_queue))

        # Create the Lambda function for size tracking
        tracking_function = Function(
            self, "BucketSizeTrackerFunction",
            runtime=Runtime.PYTHON_3_8,
            handler="size.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),
            environment={
                'DYNAMODB_TABLE_NAME': tracking_table.table_name,
                'BUCKET_NAME': bucket.bucket_name
            }
        )

        # Add the SQS queue as an event source for the Lambda function
        tracking_function.add_event_source(SqsEventSource(event_queue))

        # Grant permissions for the Lambda function to interact with resources
        tracking_table.grant_read_write_data(tracking_function)  # DynamoDB access
        topic.grant_publish(tracking_function)  # SNS access
        bucket.grant_read(tracking_function)  # S3 read access
        event_queue.grant_consume_messages(tracking_function)  # SQS access
