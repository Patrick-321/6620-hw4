import boto3
import os

def handler(event, context):
    lambda_client = boto3.client('lambda')
    
    # Get function name and API URL from the event
    function_name = event['ResourceProperties']['LambdaFunctionName']
    api_url = event['ResourceProperties']['ApiUrl']
    
    # Update environment variables for the driver lambda
    response = lambda_client.update_function_configuration(
        FunctionName=function_name,
        Environment={
            'Variables': {
                'PLOT_API_URL': api_url
            }
        }
    )
    
    return {
        'Status': 'SUCCESS',
        'Data': response
    }