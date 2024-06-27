import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('METADATA_TABLE')
table = dynamodb.Table(table_name)
s3_client = boto3.client('s3')
bucket_name = os.environ.get('CONTENT_BUCKET')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  # Allow all origins
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    try:
        # Extract query parameters
        query_params = event.get('queryStringParameters', {})

        # Construct filter expression
        filter_expression = None
        filters = ['title', 'description', 'actors', 'director', 'genre']

        for key in filters:
            if key in query_params:
                if filter_expression:
                    filter_expression &= Attr(key).contains(query_params[key])
                else:
                    filter_expression = Attr(key).contains(query_params[key])

        if filter_expression:
            response = table.scan(FilterExpression=filter_expression)
        else:
            response = table.scan()

        items = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=filter_expression,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))

        return {
            'statusCode': 200,
            'body': json.dumps(items),
            'headers': headers
        }

    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }
