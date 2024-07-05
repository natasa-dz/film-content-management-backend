# DynamoDB Schema
# ------------------ Subscriptions Table -----------------------------
# user_id (Partition Key)
# subscription_type (Range Key): e.g., actor, director, genre
# subscription_value: e.g., specific actor's name, director's name, genre

import json
import boto3
from botocore.exceptions import ClientError
import json
import os
import boto3
import logging

cognito = boto3.client('cognito-idp')
user_pool_id = os.environ['USER_POOL_ID']


sns = boto3.client('sns')
sns_topic_arn = os.environ['SNS_TOPIC_ARN']

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['SUBSCRIPTIONS_TABLE']
table = dynamodb.Table(table_name)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_email_by_username(username):
    try:
        response = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        for attribute in response['UserAttributes']:
            if attribute['Name'] == 'email':
                print(f"Email found for user {username}: {attribute['Value']}")
                return attribute['Value']
    except cognito.exceptions.UserNotFoundException:
        print(f"User {username} not found in Cognito.")
    except Exception as e:
        print(f"Error retrieving email for user {username}: {str(e)}")
    return None

def handler(event, context):
    headers={
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    # Handle preflight request
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers
        }

    body = json.loads(event['body'])
    user_id = body['user_id']
    subscription_type = body['subscription_type']
    subscription_value = body['subscription_value']
    
    try:
        table.put_item(
            Item={
                'user_id': user_id,
                'subscription_type': subscription_type,
                'subscription_value': subscription_value
            }
        )

        # Subscribe the user to the SNS topic
        sns.subscribe(
            TopicArn=sns_topic_arn,
            Protocol='email',  # or 'sms', 'http', etc.
            Endpoint=get_email_by_username(user_id)
        )

        response = {
            'statusCode': 200,
            'body': json.dumps({'message': 'Subscription added successfully'}),
            'headers': headers

        }
    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers

        }

    return response
