from aws_cdk import (
    core,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_iam as iam

)
from aws_cdk.core import Stack
from constructs import Construct
import json
from botocore.credentials import Credentials
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import get_session
import requests


class FilmContentManagementStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        AWS_ACCESS_KEY_NATASA = 'AKIA6GBMCEK55KWUXYIF'
        AWS_SECRET_KEY_NATASA='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'

        
        # KREIRANJE S3 I METADATA TABELE ZA DYNAMO-DB
        content_bucket = s3.Bucket(self, "ContentBucket")

        metadata_table = dynamodb.Table(
            self, "MetadataTable",
            table_name="MetaDataFilms",
            partition_key={"name": "film_id", "type": dynamodb.AttributeType.STRING}
        )

        # Create the IAM role for Lambda execution
        # lambda_execution_role = iam.Role(
        #     self, "FilmContentManagementLambdaExecutionRole",
        #     assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        #     description="IAM role for Lambda execution",
        #     managed_policies=[
        #         iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
        #         iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
        #     ]
        # )

        # # DescribeStacks IAM policy
        # describe_stacks_policy = iam.PolicyStatement(
        #     actions=["cloudformation:DescribeStacks"],
        #     resources=["*"]  # Adjust the resource ARN as needed
        # )

        # IAM policy for DynamoDB PutItem
        # put_item_policy = iam.PolicyStatement(
        #     actions=["dynamodb:PutItem"],
        #     resources=[metadata_table.table_arn]
        # )
        
        # lambda_execution_role.add_to_policy(put_item_policy)
        # lambda_execution_role.add_to_policy(describe_stacks_policy)


        # IAM Role for Lambda Functions
        # lambda_role = iam.Role(
        #     self, "LambdaRole",
        #     assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        # )
        
        # lambda_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        # )

        # lambda_role.add_to_policy(
        #     iam.PolicyStatement(
        #         effect=iam.Effect.ALLOW,
        #         actions=[
        #             "dynamodb:DescribeTable",
        #             "dynamodb:Query",
        #             "dynamodb:Scan",
        #             "dynamodb:GetItem",
        #             "dynamodb:PutItem",
        #             "dynamodb:UpdateItem",
        #             "dynamodb:DeleteItem"
        #         ],
        #         resources=[metadata_table.table_arn]
        #     )
        # )

        # lambda_role.add_to_policy(
        #     iam.PolicyStatement(
        #         actions=["cloudformation:DescribeStacks"],
        #         resources=["*"]
        #     )
        # )

        # Lambda funkcije za CREATE, UPDATE I GET
        create_film_function = _lambda.Function(
            self, "CreateFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="create_film_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'CONTENT_BUCKET': content_bucket.bucket_name,
                'METADATA_TABLE': metadata_table.table_name
            }
        )

        update_film_function=_lambda.Function(
            self, "UpdateFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="update_film_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'METADATA_TABLE': metadata_table.table_name
            }
        )

        get_film_function=_lambda.Function(
            self, "GetFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="get_film_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'METADATA_TABLE': metadata_table.table_name
            }
        )

        # DODELA PERMISIJA S3 I DYNAMO DB-U
        content_bucket.grant_read_write(create_film_function)

        metadata_table.grant_full_access(create_film_function)

        metadata_table.grant_read_data(update_film_function)
        metadata_table.grant_write_data(update_film_function)

        metadata_table.grant_read_data(get_film_function)

        # KREIRANJE API GATEWAY-A
        api = apigateway.RestApi(self, "FilmContentApi",
        rest_api_name="Film Content Service",
        description="This service serves film content.",
            endpoint_types=[apigateway.EndpointType.REGIONAL])
        
        #  default_cors_preflight_options={
        #         "allow_origins": apigateway.Cors.ALL_ORIGINS,
        #         "allow_methods": apigateway.Cors.ALL_METHODS,  # Also allow GET, PUT, DELETE, etc.
        #         # "allow_headers": ["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
        #     }

        # DEFINISANJE API RESURSA
        create_integration = apigateway.LambdaIntegration(create_film_function)
        update_integration = apigateway.LambdaIntegration(update_film_function)
        get_film_integration = apigateway.LambdaIntegration(get_film_function)


        films = api.root.add_resource("films")
        films.add_method("POST", create_integration)  # POST /films

        metadata = films.add_resource("{film_id}")
        metadata.add_method("PATCH", update_integration)  # PATCH /films/{film_id}
        metadata.add_method("GET", get_film_integration)  # GET /films/{film_id}



        # S3 bucket name and DynamoDB table name
        core.CfnOutput(self, "ContentBucketName", value=content_bucket.bucket_name)
        core.CfnOutput(self, "MetadataTableName", value=metadata_table.table_name)
        core.CfnOutput(self, "ApiUrl", value=api.url)









