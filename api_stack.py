from aws_cdk import Stack, CfnOutput
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration
from aws_cdk.aws_lambda import Function
from constructs import Construct

class PlotApiStack(Stack):
    def __init__(self, scope: Construct, stack_id: str, lambda_function: Function, **kwargs):
        super().__init__(scope, stack_id, **kwargs)

        # Create an API Gateway for the plotting service
        api_gateway = RestApi(self, "PlottingApiGateway",
            rest_api_name="Plotting Service API",
            description="API Gateway that triggers the Plotting Lambda function."
        )

        # Add a "plot" resource to the API
        plot_endpoint = api_gateway.root.add_resource("plot")
        lambda_integration = LambdaIntegration(lambda_function)
        plot_endpoint.add_method("POST", lambda_integration)  

        # Store API URL and ID as attributes
        self.api_url = f"{api_gateway.url}plot"
        self.api_id = api_gateway.rest_api_id

        # Output the API ID to CloudFormation
        CfnOutput(self, "ApiGatewayId", value=self.api_id)
