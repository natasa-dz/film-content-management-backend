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

        filter_expression = None
        expression_attribute_values = {}

        if 'title' in query_params:
            filter_expression = Attr('title').contains(query_params['title'])
            expression_attribute_values[':title'] = query_params['title']

        if 'description' in query_params:
            if filter_expression:
                filter_expression &= Attr('description').contains(query_params['description'])
            else:
                filter_expression = Attr('description').contains(query_params['description'])
            expression_attribute_values[':description'] = query_params['description']

        if 'actors' in query_params:
            if filter_expression:
                filter_expression &= Attr('actors').contains(query_params['actors'])
            else:
                filter_expression = Attr('actors').contains(query_params['actors'])
            expression_attribute_values[':actors'] = query_params['actors']

        if 'director' in query_params:
            if filter_expression:
                filter_expression &= Attr('director').contains(query_params['director'])
            else:
                filter_expression = Attr('director').contains(query_params['director'])
            expression_attribute_values[':director'] = query_params['director']

        if 'genre' in query_params:
            if filter_expression:
                filter_expression &= Attr('genre').contains(query_params['genre'])
            else:
                filter_expression = Attr('genre').contains(query_params['genre'])
            expression_attribute_values[':genre'] = query_params['genre']

        if filter_expression:
            response = table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
        else:
            response = table.scan()

        return {
            'statusCode': 200,
            'body': json.dumps(response['Items']),
            'headers': headers
        }

    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }
