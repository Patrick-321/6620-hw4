from aws_cdk import Stack, Duration
from aws_cdk.aws_s3 import Bucket, EventType
from aws_cdk.aws_s3_notifications import SnsDestination
from aws_cdk.aws_sns import Topic
from constructs import Construct

class NotificationEnabledStorageStack(Stack):
    def __init__(self, scope: Construct, stack_id: str, **kwargs):
        super().__init__(scope, stack_id, **kwargs)

        # Create an S3 bucket for storage
        storage_bucket = Bucket(self, "NotificationBucket")

        # Create an SNS topic for bucket events
        bucket_event_topic = Topic(self, "S3BucketEventTopic")

        # Configure the S3 bucket to send notifications for object events to the SNS topic
        storage_bucket.add_event_notification(EventType.OBJECT_CREATED, SnsDestination(bucket_event_topic))
        storage_bucket.add_event_notification(EventType.OBJECT_REMOVED, SnsDestination(bucket_event_topic))

        # Expose the bucket and topic as attributes
        self.bucket = storage_bucket
        self.topic = bucket_event_topic
