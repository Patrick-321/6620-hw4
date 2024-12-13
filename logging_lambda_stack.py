from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_sqs as sqs,
    aws_cloudwatch as cloudwatch,
)
import aws_cdk.aws_cloudwatch_actions as cloudwatch_actions
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from aws_cdk.aws_sqs import Queue
from aws_cdk.aws_sns import Topic
from aws_cdk.aws_sns_subscriptions import SqsSubscription, LambdaSubscription
from aws_cdk.aws_s3 import Bucket
from constructs import Construct

class LogHandlerStack(Stack):
    def __init__(self, scope: Construct, stack_id: str, sns_topic: Topic, bucket: Bucket, **kwargs):
        super().__init__(scope, stack_id, **kwargs)

        # Create an SQS queue and subscribe it to the provided SNS topic
        event_queue = Queue(self, "BucketEventQueue", visibility_timeout=Duration.seconds(300))
        sns_topic.add_subscription(SqsSubscription(event_queue))

        # Create a Lambda function for handling logging
        logging_function = lambda_.Function(
            self, "LoggingFunction",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="logging.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(60),
            environment={
                'BUCKET_NAME': bucket.bucket_name
            }
        )
        bucket.grant_read_write(logging_function)

        # Configure the logging Lambda to process events from the SQS queue
        logging_function.add_event_source(SqsEventSource(event_queue))

        # Create a Log Group for the Logging Lambda
        log_group = logs.LogGroup(
            self, "LoggingFunctionLogGroup",
            log_group_name=f"/aws/lambda/{logging_function.function_name}",
            retention=logs.RetentionDays.ONE_WEEK
        )

        # Add a Metric Filter to monitor size_delta values in logs
        metric_filter = logs.MetricFilter(
            self, "SizeDeltaMetric",
            log_group=log_group,
            metric_namespace="BucketMetrics",
            metric_name="ObjectSizeChanges",
            filter_pattern=logs.FilterPattern.exists("$.size_delta"),  # Check if size_delta exists
            metric_value="$.size_delta"
        )

        # Create a Lambda function for cleaning up bucket data
        cleanup_function = lambda_.Function(
            self, "CleanupFunction",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="cleaner.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(60),
            environment={
                'BUCKET_NAME': bucket.bucket_name
            }
        )
        bucket.grant_read_write(cleanup_function)
        bucket.grant_delete(cleanup_function)

        # Create an SNS topic for triggering the Cleanup Lambda
        cleanup_alarm_topic = Topic(self, "CleanupAlarmTopic")

        # Subscribe the Cleanup Lambda to the alarm topic
        cleanup_alarm_topic.add_subscription(LambdaSubscription(cleanup_function))

        # Define a CloudWatch alarm based on the ObjectSizeChanges metric
        size_alarm = cloudwatch.Alarm(
            self, "ObjectSizeAlarm",
            metric=cloudwatch.Metric(
                namespace="BucketMetrics",
                metric_name="ObjectSizeChanges",
                statistic="Sum",
                period=Duration.seconds(10),
            ),
            threshold=15,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        # Trigger the Cleanup Lambda when the alarm is raised
        size_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(cleanup_alarm_topic)
        )
