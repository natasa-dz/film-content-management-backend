from aws_cdk import (
    core,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_iam as iam
    )

from aws_cdk.core import Stack
from aws_cdk.core import RemovalPolicy

from constructs import Construct

class FilmContentManagementStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # Create S3 bucket with CORS configuration
        content_bucket = s3.Bucket(
            self,"ContentBucket",
            bucket_name="content-bucket-cloud-film-app",
            
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.DELETE,
                        s3.HttpMethods.HEAD,
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"]
                )
            ],
            removal_policy=RemovalPolicy.DESTROY   
        )

        # DynamoDB creation
        metadata_table = dynamodb.Table(
            self, "MetadataTable",
            table_name="MetaDataFilms",
            partition_key={"name": "film_id", "type": dynamodb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY  
        )

        # Create a Cognito User Pool
        user_pool = cognito.UserPool(self, "UserPool",
            user_pool_name="FilmContentManagementUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True
            ),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                )
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            custom_attributes={
                "confirmation_status": cognito.StringAttribute(
                    min_len=1,
                    mutable=True
                )
            }
        )

        # COGNITO IAM POLICY
        cognito_policy = iam.PolicyStatement(
            actions=[
                "cognito-idp:AdminAddUserToGroup",
                "cognito-idp:AdminCreateUser",
                "cognito-idp:AdminDeleteUser",
                "cognito-idp:AdminConfirmSignUp",
                "cognito-idp:AdminInitiateAuth",
                "cognito-idp:AdminRespondToAuthChallenge",
                "cognito-idp:AdminUpdateUserAttributes"
            ],
            resources=[
                user_pool.user_pool_arn  # ARN of your Cognito User Pool
            ]
        )

        # Create a User Pool Client
        user_pool_client = user_pool.add_client("UserPoolClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            )
        )

        # Create IAM roles for the user groups
        admin_role = iam.Role(self, "AdminRole",
            assumed_by=iam.ServicePrincipal("cognito-idp.amazonaws.com")
        )
        user_role = iam.Role(self, "UserRole",
            assumed_by=iam.ServicePrincipal("cognito-idp.amazonaws.com")
        )

        # Attach policies to the roles
        admin_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"))
        user_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"))

        # Create user groups and attach IAM roles
        admin_group = cognito.CfnUserPoolGroup(self, "AdminGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="Admin",
            role_arn=admin_role.role_arn
        )
        user_group = cognito.CfnUserPoolGroup(self, "UserGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="User",
            role_arn=user_role.role_arn
        )

        # Lambda function for LOGIN and REGISTRATION
        registration_login_lambda = _lambda.Function(self, "RegistrationLoginHandler",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="login_registration_handler.handler",
            code=_lambda.Code.from_asset("lambda"), 
            environment={
                'USER_POOL_ID': user_pool.user_pool_id,
                'USER_POOL_CLIENT_ID': user_pool_client.user_pool_client_id
            }
        )
        registration_login_lambda.role.add_to_policy(cognito_policy)


        # Lambda functions for CREATE, UPDATE, and GET
        create_film_function = _lambda.Function(
            self, "CreateFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="create_film_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'CONTENT_BUCKET': content_bucket.bucket_name,
                'METADATA_TABLE': metadata_table.table_name,
            }
        )

        update_film_function = _lambda.Function(
            self, "UpdateFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="update_film_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'CONTENT_BUCKET': content_bucket.bucket_name,
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

        delete_film_function = _lambda.Function(
            self, "DeleteFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="delete_film_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'METADATA_TABLE': metadata_table.table_name,
                'CONTENT_BUCKET': content_bucket.bucket_name

            }
        )

        search_film_function = _lambda.Function(
            self, "SearchFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="search_film_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'CONTENT_BUCKET': content_bucket.bucket_name,
                'METADATA_TABLE': metadata_table.table_name
            }
        )

        # Grant permissions to Lambda functions

        # grants content bucket
        content_bucket.grant_read_write(create_film_function)
        content_bucket.grant_read_write(update_film_function)

        content_bucket.grant_delete(delete_film_function)

        content_bucket.grant_read(get_film_function)
        content_bucket.grant_read(search_film_function)

        # grants dynamoDB
        metadata_table.grant_full_access(create_film_function)
        metadata_table.grant_read_data(search_film_function)

        metadata_table.grant_full_access(delete_film_function)
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

        search = api.root.add_resource("search")
        search.add_method("GET", apigateway.LambdaIntegration(search_film_function))

        register = api.root.add_resource("register")
        register_integration = apigateway.LambdaIntegration(registration_login_lambda)
        register.add_method("POST", register_integration)

        login = api.root.add_resource("login")
        login_integration = apigateway.LambdaIntegration(registration_login_lambda)
        login.add_method("POST", login_integration)


        film = films.add_resource("{film_id}")
        film.add_method("PATCH", apigateway.LambdaIntegration(update_film_function))
        film.add_method("GET", apigateway.LambdaIntegration(get_film_function))
        film.add_method("DELETE", apigateway.LambdaIntegration(delete_film_function))

        download = api.root.add_resource("download")
        download.add_method("GET", apigateway.LambdaIntegration(get_film_function))


        # Outputs
        core.CfnOutput(self, "ContentBucketName", value=content_bucket.bucket_name)
        core.CfnOutput(self, "MetadataTableName", value=metadata_table.table_name)
        core.CfnOutput(self, "ApiUrl", value=api.url)
        core.CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        core.CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
        core.CfnOutput(self, "RegistrationLoginApiUrl", value=api.url)

