import aws_cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_lambda_event_sources as lambda_event_sources,
    aws_sns as sns
    )

from aws_cdk import Stack
from aws_cdk import RemovalPolicy

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
        movie_table = dynamodb.Table(
            self, "MoviesTable",
            table_name="MovieTable",
            partition_key={"name": "film_id", "type": dynamodb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY,  # Example policy, adjust as needed
            read_capacity=1,  # Example capacity, adjust as needed
            write_capacity=1,  # Example capacity, adjust as needed
            stream=dynamodb.StreamViewType.NEW_IMAGE,  # Enable streams if needed
        )

        # Add Global Secondary Index (GSI) for querying by film_type
        movie_table.add_global_secondary_index(
            index_name="FilmTypeIndex",
            partition_key=dynamodb.Attribute(
                name="film_type",
                type=dynamodb.AttributeType.STRING
            ),
            read_capacity=1,
            write_capacity=1
        )


        review_table = dynamodb.Table(
            self, "ReviewTable",
            table_name="ReviewTable",
            partition_key={"name": "review_id", "type": dynamodb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY,
            read_capacity=1,
            write_capacity=1
        )
        review_table.add_global_secondary_index(
            index_name="ReviewTypeIndex",
            partition_key=dynamodb.Attribute(
                name="review_type",
                type=dynamodb.AttributeType.STRING
            ),
            read_capacity=1,
            write_capacity=1
        )

        subscription_table = dynamodb.Table(
            self, "SubscriptionsTable",
            table_name="SubscriptionsTable",
            partition_key={"name": "user_id", "type": dynamodb.AttributeType.STRING},
            sort_key={"name": "subscription_type", "type": dynamodb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY,
            read_capacity=1,
            write_capacity=1
        )
        subscription_table.add_global_secondary_index(
            index_name="SubscriptionsTypeIndex",
            partition_key=dynamodb.Attribute(
                name="subscriptions_type",
                type=dynamodb.AttributeType.STRING
            ),
            read_capacity=1,
            write_capacity=1
        )


        # Add the user feed table
        user_feed_table = dynamodb.Table(
            self, "UserFeedTable",
            table_name="UserFeedTable",
            partition_key={"name": "user_id", "type": dynamodb.AttributeType.STRING},
            sort_key={"name": "score", "type": dynamodb.AttributeType.NUMBER},
            removal_policy=RemovalPolicy.DESTROY,
            read_capacity=1,
            write_capacity=1
        )
        user_feed_table.add_global_secondary_index(
            index_name="UserFeedTypeIndex",
            partition_key=dynamodb.Attribute(
                name="user_feed_type",
                type=dynamodb.AttributeType.STRING
            ),
            read_capacity=1,
            write_capacity=1
        )

        # Add the download history table
        download_history_table = dynamodb.Table(
            self, "DownloadHistoryTable",
            table_name="DownloadHistoryTable",
            partition_key={"name": "user_id", "type": dynamodb.AttributeType.STRING},
            sort_key={"name": "download_time", "type": dynamodb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY,
            read_capacity=1,
            write_capacity=1
        )
        download_history_table.add_global_secondary_index(
            index_name="DownloadTypeIndex",
            partition_key=dynamodb.Attribute(
                name="download_type",
                type=dynamodb.AttributeType.STRING
            ),
            read_capacity=1,
            write_capacity=1
        )
# ----------------- review functions
        review_function = _lambda.Function(
            self, "ReviewFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="review_handler.handler",
            code=_lambda.Code.from_asset("review_service"),
            environment={
                'REVIEW_TABLE': review_table.table_name,
                'MOVIE_TABLE': movie_table.table_name
            }
        )


# ----------------- notification functions

        sns_topic = sns.Topic(self, "FilmSubscriptionTopic",
            display_name="Film Subscription Notifications"
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
                ),
                'role': cognito.StringAttribute(min_len=1, max_len=20)

            }
        )


        # Lambda function to process DynamoDB Stream
        notification_function = _lambda.Function(
            self, "NotificationFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="notification_handler.handler",
            code=_lambda.Code.from_asset("subscription_service"),
            environment={
                'SUBSCRIPTIONS_TABLE': subscription_table.table_name,
                'SNS_TOPIC_ARN': sns_topic.topic_arn,
                'USER_POOL_ID': user_pool.user_pool_id
            }
        )

        # Add DynamoDB stream as an event source for the Lambda function
        notification_function.add_event_source(
            lambda_event_sources.DynamoEventSource(
                movie_table,
                starting_position=_lambda.StartingPosition.TRIM_HORIZON,
                batch_size=5,
                retry_attempts=10
            )
            )

        # COGNITO IAM POLICY
        cognito_policy = iam.PolicyStatement(
            actions=[
                "cognito-idp:AdminAddUserToGroup",
                "cognito-idp:AdminCreateUser",
                "cognito-idp:SignUp",
                "cognito-idp:AdminGetUser",
                "cognito-idp:AdminListGroupsForUser",
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
            code=_lambda.Code.from_asset("cognito_service"),
            environment={
                'USER_POOL_ID': user_pool.user_pool_id,
                'USER_POOL_CLIENT_ID': user_pool_client.user_pool_client_id
            }
        )

        # Lambda user role fetch
        user_role_fetch_lambda = _lambda.Function(
            self, "UserRoleFetchHandler",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="get_user_role_handler.handler",
            code=_lambda.Code.from_asset("cognito_service"),
            environment={
                'USER_POOL_ID': user_pool.user_pool_id,
                'USER_POOL_CLIENT_ID': user_pool_client.user_pool_client_id
            }
        )

        # Lambda functions for CREATE, UPDATE, and GET
        create_film_function = _lambda.Function(
            self, "CreateFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="create_film_handler.handler",
            code=_lambda.Code.from_asset("film_service"),
            environment={
                'CONTENT_BUCKET': content_bucket.bucket_name,
                'METADATA_TABLE': movie_table.table_name,
                'USER_POOL_ID': user_pool.user_pool_id,
                'USER_POOL_CLIENT_ID': user_pool_client.user_pool_client_id,
                'SUBSCRIPTIONS_TABLE': subscription_table.table_name,
                'SNS_TOPIC_ARN': sns_topic.topic_arn  # Add SNS topic ARN as environment variable

            },
            timeout=aws_cdk.Duration.seconds(900)  # Set timeout to 5 minutes (15 min = 900s maximum allowed)
        )

        # Transcode Lambda function
        transcode_function = _lambda.Function(
            self, "TranscodeFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="transcode_handler.handler",
            code=_lambda.Code.from_asset("transcoding_service"),
            timeout=aws_cdk.Duration.minutes(15),
            environment={
                'CONTENT_BUCKET': content_bucket.bucket_name,
            }
        )

        update_film_function = _lambda.Function(
            self, "UpdateFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="update_film_handler.handler",
            code=_lambda.Code.from_asset("film_service"),
            environment={
                'CONTENT_BUCKET': content_bucket.bucket_name,
                'METADATA_TABLE': movie_table.table_name
            }
        )

        get_film_function = _lambda.Function(
            self, "GetFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="get_film_handler.handler",
            code=_lambda.Code.from_asset("film_service"),
            environment={
                'METADATA_TABLE': movie_table.table_name,
                'CONTENT_BUCKET': content_bucket.bucket_name,
                'DOWNLOAD_HISTORY_TABLE': download_history_table.table_name

            }
        )

        delete_film_function = _lambda.Function(
            self, "DeleteFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="delete_film_handler.handler",
            code=_lambda.Code.from_asset("film_service"),
            environment={
                'METADATA_TABLE': movie_table.table_name,
                'CONTENT_BUCKET': content_bucket.bucket_name

            }
        )

        search_film_function = _lambda.Function(
            self, "SearchFilmFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="search_film_handler.handler",
            code=_lambda.Code.from_asset("film_service"),
            environment={
                'CONTENT_BUCKET': content_bucket.bucket_name,
                'METADATA_TABLE': movie_table.table_name
            }
        )

        generate_feed_function = _lambda.Function(
            self, "GenerateUserFeed",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="generate_feed_handler.handler",
            code=_lambda.Code.from_asset("feed_service"),
            environment={
                'SUBSCRIPTIONS_TABLE': subscription_table.table_name,
                'METADATA_TABLE':movie_table.table_name,
                'REVIEW_TABLE':review_table.table_name,
                'USER_FEED_TABLE':user_feed_table.table_name,
                'USER_DOWNLOADS_TABLE':download_history_table.table_name
            }
        )        # Grant permissions to Lambda functions

        get_feed_function = _lambda.Function(
            self, "GetUserFeed",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="get_feed_handler.handler",
            code=_lambda.Code.from_asset("feed_service"),
            environment={
                'USER_FEED_TABLE':user_feed_table.table_name,
            }
        )
        # Lambda functions for subscription management
        create_subscription_function = _lambda.Function(
            self, "CreateSubscriptionFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="create_subscription_handler.handler",
            code=_lambda.Code.from_asset("subscription_service"),
            environment={
                'SUBSCRIPTIONS_TABLE': subscription_table.table_name,
                'SNS_TOPIC_ARN': sns_topic.topic_arn,  # Add SNS topic ARN as environment variable,
                'USER_POOL_ID': user_pool.user_pool_id

            }
        )

        create_subscription_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sns:Subscribe"],
                resources=[sns_topic.topic_arn]
            )
        )

        delete_subscription_function = _lambda.Function(
            self, "DeleteSubscriptionFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="delete_subscription_handler.handler",
            code=_lambda.Code.from_asset("subscription_service"),
            environment={
                'SUBSCRIPTIONS_TABLE': subscription_table.table_name
            }
        )

        list_subscriptions_function = _lambda.Function(
            self, "ListSubscriptionsFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="get_subscriptions_handler.handler",
            code=_lambda.Code.from_asset("subscription_service"),
            environment={
                'SUBSCRIPTIONS_TABLE': subscription_table.table_name
            }
        )

        # GIVE ADMIN COGNITO POLICY!!!!
        registration_login_lambda.role.add_to_policy(cognito_policy)
        user_role_fetch_lambda.role.add_to_policy(cognito_policy)
        create_film_function.role.add_to_policy(cognito_policy)
        create_subscription_function.role.add_to_policy(cognito_policy)
        notification_function.role.add_to_policy(cognito_policy)

        # grants content bucket
        content_bucket.grant_read_write(create_film_function)
        content_bucket.grant_read_write(update_film_function)

        content_bucket.grant_delete(delete_film_function)

        content_bucket.grant_read(get_film_function)
        content_bucket.grant_read(search_film_function)

        content_bucket.grant_read(generate_feed_function)
        content_bucket.grant_read_write(transcode_function)

        # Grant publish permissions to your transcode Lambda function
        sns_topic.grant_publish(create_film_function)
        sns_topic.grant_publish(notification_function)



        # grants dynamoDB

        # -------------------- movie service grants
        movie_table.grant_full_access(create_film_function)
        movie_table.grant_read_data(search_film_function)

        movie_table.grant_full_access(delete_film_function)
        movie_table.grant_read_write_data(update_film_function)

        movie_table.grant_read_data(get_film_function)

        movie_table.grant_read_data(generate_feed_function)

        transcode_function.grant_invoke(create_film_function)
        download_history_table.grant_full_access(get_film_function)
        download_history_table.grant_read_data(generate_feed_function)

        # ------------------ review service grants
        review_table.grant_read_data(generate_feed_function)
        review_table.grant_full_access(review_function)
        movie_table.grant_read_data(review_function)

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

        #notify users about subscriptions
        subscription_table.grant_full_access(notification_function)
        # Grant permissions to subscription Lambda functions
        subscription_table.grant_full_access(create_subscription_function)
        subscription_table.grant_full_access(delete_subscription_function)
        subscription_table.grant_read_data(list_subscriptions_function)
        subscription_table.grant_read_data(generate_feed_function)
        subscription_table.grant_read_data(create_film_function)

        # feed grants
        user_feed_table.grant_full_access(generate_feed_function)
        user_feed_table.grant_read_data(get_feed_function)
        user_feed_table.grant_read_write_data(create_subscription_function)
        user_feed_table.grant_read_write_data(get_film_function)
        user_feed_table.grant_read_write_data(review_function)


# ------------------- API METHODS

        # Lambda funkcija za autorizaciju
        auth_lambda_admin = _lambda.Function(
            self, "AuthFunctionAdmin",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="authorization_admin.permission_handler",
            code=_lambda.Code.from_asset("authorization"),
            environment={
                'USER_POOL_ID': user_pool.user_pool_id,
            }
        )

        # Definisanje Lambda authorizera
        authorizer_admin = apigateway.TokenAuthorizer(
            self, "APIGatewayAuthorizerAdmin",
            handler=auth_lambda_admin,
            identity_source=apigateway.IdentitySource.header("Authorization")
        )

        # Lambda funkcija za autorizaciju
        auth_lambda_user = _lambda.Function(
            self, "AuthFunctionUser",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="authorization_user.permission_handler",
            code=_lambda.Code.from_asset("authorization"),
            environment={
                'USER_POOL_ID': user_pool.user_pool_id,
            }
        )

        # Definisanje Lambda authorizera
        authorizer_user = apigateway.TokenAuthorizer(
            self, "APIGatewayAuthorizerUser",
            handler=auth_lambda_user,
            identity_source=apigateway.IdentitySource.header("Authorization")
        )

        # Definisanje endpoint-a za kreiranje filma
        films = api.root.add_resource("films")
        create_film_integration = apigateway.LambdaIntegration(create_film_function)
        films.add_method(
            "POST",
            create_film_integration,
            authorization_type=apigateway.AuthorizationType.CUSTOM,
            authorizer=authorizer_admin
        )

        get_film_integration = apigateway.LambdaIntegration(get_film_function)
        films.add_method(
            "GET",
            get_film_integration
        )

        search = api.root.add_resource("search")
        search_film_integration = apigateway.LambdaIntegration(search_film_function)
        search.add_method(
            "GET",
            search_film_integration,
            authorization_type=apigateway.AuthorizationType.CUSTOM,
            authorizer=authorizer_user
        )

        film = films.add_resource("{film_id}")
        update_film_integration = apigateway.LambdaIntegration(update_film_function)
        film.add_method(
            "PATCH",
            update_film_integration,
            authorization_type=apigateway.AuthorizationType.CUSTOM,
            authorizer=authorizer_admin
        )

        get_film_integration = apigateway.LambdaIntegration(get_film_function)
        film.add_method(
            "GET",
            get_film_integration
        )

        delete_film_integration = apigateway.LambdaIntegration(delete_film_function)
        film.add_method(
            "DELETE",
            delete_film_integration,
            authorization_type=apigateway.AuthorizationType.CUSTOM,
            authorizer=authorizer_admin
        )

        download = api.root.add_resource("download")
        download_integration = apigateway.LambdaIntegration(get_film_function)
        download.add_method(
            "GET",
            download_integration,
            authorization_type = apigateway.AuthorizationType.CUSTOM,
            authorizer = authorizer_user
        )
# ----------- cognito
        confirm_resource = api.root.add_resource("confirm")
        confirm_integration = apigateway.LambdaIntegration(registration_login_lambda)
        confirm_resource.add_method(
            "POST",
            confirm_integration
        )

        register = api.root.add_resource("register")
        register_integration = apigateway.LambdaIntegration(registration_login_lambda)
        register.add_method(
            "POST",
            register_integration
        )

        login = api.root.add_resource("login")
        login_integration = apigateway.LambdaIntegration(registration_login_lambda)
        login.add_method("POST",
                         login_integration
        )

        fetch_role=api.root.add_resource("fetch-role")
        fetch_role_integration = apigateway.LambdaIntegration(user_role_fetch_lambda)
        fetch_role.add_method('GET'
                              , fetch_role_integration)


        subscriptions = api.root.add_resource("subscriptions")
        subscriptions.add_method("POST"
                                 ,apigateway.LambdaIntegration(create_subscription_function),
                                 authorization_type=apigateway.AuthorizationType.CUSTOM,
                                 authorizer=authorizer_user
                                 )
        subscriptions.add_method("GET",
                                 apigateway.LambdaIntegration(list_subscriptions_function),
                                 authorization_type=apigateway.AuthorizationType.CUSTOM,
                                 authorizer=authorizer_user)
        subscriptions.add_method("DELETE",
                                 apigateway.LambdaIntegration(delete_subscription_function),
                                 authorization_type=apigateway.AuthorizationType.CUSTOM,
                                 authorizer=authorizer_user)


# ----------- reviews
        reviews = film.add_resource("reviews")
        reviews.add_method("POST",
                           apigateway.LambdaIntegration(review_function),
                                 authorization_type=apigateway.AuthorizationType.CUSTOM,
                                 authorizer=authorizer_user)

# ----------- feed
        generate_feed = api.root.add_resource("generate-feed")

        generate_feed.add_method("POST",
                                 apigateway.LambdaIntegration(generate_feed_function),
                                 authorization_type=apigateway.AuthorizationType.CUSTOM,
                                 authorizer=authorizer_user)


        get_feed = api.root.add_resource("get-feed")
        get_feed.add_method("GET",
                            apigateway.LambdaIntegration(get_feed_function),
                                 authorization_type=apigateway.AuthorizationType.CUSTOM,
                                 authorizer=authorizer_user)

# ----------- transcoding
        transcoder=films.add_resource("transcode")
        transcoder.add_method("POST",
                              apigateway.LambdaIntegration(transcode_function),
                                 authorization_type=apigateway.AuthorizationType.CUSTOM,
                                 authorizer=authorizer_user)


    # Outputs
        aws_cdk.CfnOutput(self, "ContentBucketName", value=content_bucket.bucket_name)
        aws_cdk.CfnOutput(self, "MetadataTableName", value=movie_table.table_name)
        aws_cdk.CfnOutput(self, "ReviewTableName", value=review_table.table_name)
        aws_cdk.CfnOutput(self, "SubscriptionsTableName", value=subscription_table.table_name)
        aws_cdk.CfnOutput(self, "ApiUrl", value=api.url)
        aws_cdk.CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        aws_cdk.CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
        aws_cdk.CfnOutput(self, "RegistrationLoginApiUrl", value=api.url)
