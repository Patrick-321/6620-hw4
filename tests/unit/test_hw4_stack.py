import aws_cdk as cdk
import aws_cdk.assertions as test_assertions

from hw4.hw4_stack import Hw4Stack

# Example unit tests. To execute these tests, uncomment this code along with 
# the example resource definition in hw4/hw4_stack.py.
def test_queue_created_in_stack():
    app = cdk.App()
    test_stack = Hw4Stack(app, "hw4")
    template = test_assertions.Template.from_stack(test_stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
