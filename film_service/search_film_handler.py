import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


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

        # Construct key condition expression and filter expression
        key_condition_expression = None
        filter_expression = ''
        expression_attribute_values = {}

        # Assuming the query parameter for title is mandatory for using the GSI
        if 'title' in query_params:
            key_condition_expression = Key('title').eq(query_params['title'])

            # Construct filter expression for additional filters
            filters = ['description', 'actors', 'director', 'genre']
            for key in filters:
                if key in query_params:
                    if filter_expression:
                        filter_expression += ' AND '
                    filter_expression += f"contains({key}, :{key})"
                    expression_attribute_values[f':{key}'] = query_params[key]

            # Perform query using the Global Secondary Index (GSI) for Title
            if filter_expression:
                response = table.query(
                    IndexName='TitleIndex',
                    KeyConditionExpression=key_condition_expression,
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )
            else:
                response = table.query(
                    IndexName='TitleIndex',
                    KeyConditionExpression=key_condition_expression,
                )

            items = response.get('Items', [])

            while 'LastEvaluatedKey' in response:
                if filter_expression:
                    response = table.query(
                        IndexName='TitleIndex',
                        KeyConditionExpression=key_condition_expression,
                        FilterExpression=filter_expression,
                        ExpressionAttributeValues=expression_attribute_values,
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                else:
                    response = table.query(
                        IndexName='TitleIndex',
                        KeyConditionExpression=key_condition_expression,
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                items.extend(response.get('Items', []))

            return {
                'statusCode': 200,
                'body': json.dumps(items, cls=DecimalEncoder),
                'headers': headers
            }

        else:
            # If title is not provided, return an error response
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Title is required for querying'}),
                'headers': headers
            }

    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        return {
            'statusCode': 500,
            'body': json.dumps({'error': e.response['Error']['Message']}),
            'headers': headers
        }
    except Exception as e:
        logger.error(str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }
