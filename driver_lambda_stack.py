from aws_cdk import Stack, Duration, Aws
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_iam import PolicyStatement
from constructs import Construct

class DriverFunctionStack(Stack):
    def __init__(self, scope: Construct, stack_id: str, bucket: Bucket, api_url: str, api_id: str, **kwargs):
        super().__init__(scope, stack_id, **kwargs)

        # Create the Driver Lambda function
        self.driver_function = Function(
            self, "DriverFunction",
            runtime=Runtime.PYTHON_3_8,
            handler="driver.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),
            environment={
                'BUCKET_NAME': bucket.bucket_name,
                'PLOTTING_API_URL': api_url
            }
        )

        # Grant the Lambda function write access to the S3 bucket
        bucket.grant_write(self.driver_function)
        
        # Allow the Driver Lambda function to invoke API Gateway
        self.driver_function.add_to_role_policy(PolicyStatement(
            actions=["execute-api:Invoke"],
            resources=[
                f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{api_id}/prod/*"
            ]
        ))
