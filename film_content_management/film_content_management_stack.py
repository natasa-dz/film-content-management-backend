from aws_cdk import (
    core,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    Stack
)
from constructs import Construct

class FilmContentManagementStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "FilmContentManagementQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )


        # KREIRANJE S3 I METADATA TABELE ZA DYNAMO-DB
        content_bucket = s3.Bucket(self, "ContentBucket")


        metadata_table = dynamodb.Table(
            self, "MetadataTable",
            partition_key={"name": "film_id", "type": dynamodb.AttributeType.STRING}
        )


        # Lambda funkcije za CREATE, UPDATE I GET
        create_film_function = _lambda.Function(
            self, "CreateFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="upload_handler.handler",
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
        metadata_table.grant_read_write(update_film_function)
        metadata_table.grant_read_data(get_film_function)


        # KREIRANJE API GATEWAY-A
        api = apigateway.RestApi(self, "FilmContentApi",
        rest_api_name="Film Content Service",
        description="This service serves film content.")

        # DEFINISANJE API RESURSA
        create_integration = apigateway.LambdaIntegration(create_film_function)
        update_integration = apigateway.LambdaIntegration(update_film_function)
        get_integration = apigateway.LambdaIntegration(get_film_function)

        films = api.root.add_resource("films")
        films.add_method("POST", create_integration)  # POST /films

        metadata = films.add_resource("{film_id}")
        metadata.add_method("PATCH", update_integration)  # PATCH /films/{film_id}
        metadata.add_method("GET", get_integration)  # GET /films/{film_id}


        # S3 bucket name and DynamoDB table name
        core.CfnOutput(self, "ContentBucketName", value=content_bucket.bucket_name)
        core.CfnOutput(self, "MetadataTableName", value=metadata_table.table_name)






