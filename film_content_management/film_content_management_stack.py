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

class FilmContentManagementStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket and DynamoDB table
        content_bucket = s3.Bucket(self, "ContentBucket", bucket_name="content-bucket-cloud-film-app")

        metadata_table = dynamodb.Table(
            self, "MetadataTable",
            table_name="MetaDataFilms",
            partition_key={"name": "film_id", "type": dynamodb.AttributeType.STRING}
        )

        # Lambda functions for CREATE, UPDATE, and GET
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

        update_film_function = _lambda.Function(
            self, "UpdateFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="update_film_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'METADATA_TABLE': metadata_table.table_name
            }
        )

        get_film_function = _lambda.Function(
            self, "GetFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="get_film_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'METADATA_TABLE': metadata_table.table_name,
                'CONTENT_BUCKET': content_bucket.bucket_name
            }
        )

        # Grant permissions to Lambda functions
        content_bucket.grant_read_write(create_film_function)
        metadata_table.grant_full_access(create_film_function)
        metadata_table.grant_read_write_data(update_film_function)
        metadata_table.grant_read_data(get_film_function)

        # Create API Gateway
        api = apigateway.RestApi(self, "FilmContentApi",
            rest_api_name="Film Content Service",
            description="This service serves film content.",
            endpoint_types=[apigateway.EndpointType.REGIONAL],
            default_cors_preflight_options={
                "allow_origins": apigateway.Cors.ALL_ORIGINS,
                "allow_methods": apigateway.Cors.ALL_METHODS
            }
        )

        # Define API resources and methods
        films = api.root.add_resource("films")
        films.add_method("POST", apigateway.LambdaIntegration(create_film_function))
        films.add_method("GET", apigateway.LambdaIntegration(get_film_function))


        film = films.add_resource("{film_id}")
        film.add_method("PATCH", apigateway.LambdaIntegration(update_film_function))
        film.add_method("GET", apigateway.LambdaIntegration(get_film_function))

        # Outputs
        core.CfnOutput(self, "ContentBucketName", value=content_bucket.bucket_name)
        core.CfnOutput(self, "MetadataTableName", value=metadata_table.table_name)
        core.CfnOutput(self, "ApiUrl", value=api.url)
