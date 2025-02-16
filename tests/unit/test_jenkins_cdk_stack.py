import aws_cdk as core
import aws_cdk.assertions as assertions

from jenkins_cdk.jenkins_cdk_stack import JenkinsCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in jenkins_cdk/jenkins_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = JenkinsCdkStack(app, "jenkins-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
