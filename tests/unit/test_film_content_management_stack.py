import aws_cdk as core
import aws_cdk.assertions as assertions

from film_content_management.film_content_management_stack import FilmContentManagementStack

# example tests. To run these tests, uncomment this file along with the example
# resource in film_content_management/film_content_management_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FilmContentManagementStack(app, "film-content-management")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
