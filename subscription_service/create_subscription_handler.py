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

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['SUBSCRIPTIONS_TABLE']
table = dynamodb.Table(table_name)

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
