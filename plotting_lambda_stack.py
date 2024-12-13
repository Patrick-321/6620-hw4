from aws_cdk import Stack, Duration
from aws_cdk.aws_lambda import Function, Runtime, Code, Architecture, LayerVersion
from aws_cdk.aws_dynamodb import Table
from aws_cdk.aws_s3 import Bucket
from constructs import Construct

class PlotFunctionStack(Stack):
    def __init__(self, scope: Construct, stack_id: str, table: Table, bucket: Bucket, **kwargs):
        super().__init__(scope, stack_id, **kwargs)

        # Define the ARN for the Matplotlib layer
        matplotlib_layer_arn = "arn:aws:lambda:us-west-1:188366678271:layer:matplot:4"
        matplotlib_layer = LayerVersion.from_layer_version_arn(self, "MatplotlibLayer", matplotlib_layer_arn)

        # Create a dedicated bucket for plots
        plot_storage_bucket = Bucket(self, "PlotStorageBucket", bucket_name="plothw5")

        # Define the Lambda function for plotting
        plotting_function = Function(
            self, "PlotFunction",
            runtime=Runtime.PYTHON_3_8,
            handler="plotting.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),
            architecture=Architecture.ARM_64,
            layers=[matplotlib_layer],
            environment={
                'DYNAMODB_TABLE_NAME': table.table_name,
                'PLOT_BUCKET_NAME': plot_storage_bucket.bucket_name,
                'BUCKET_NAME': bucket.bucket_name
            }
        )

        # Grant necessary permissions to the Lambda function
        plot_storage_bucket.grant_read_write(plotting_function)
        table.grant_read_write_data(plotting_function)
