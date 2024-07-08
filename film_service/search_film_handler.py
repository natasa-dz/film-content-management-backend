import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from decimal import Decimal

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('METADATA_TABLE')  # Adjust this to your table name
table = dynamodb.Table(table_name)
s3_client = boto3.client('s3')
bucket_name = os.environ.get('CONTENT_BUCKET')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

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
        title = query_params.get('title', '')
        description = query_params.get('description', '')
        actors = query_params.get('actors', '')
        director = query_params.get('director', '')
        genre = query_params.get('genre', '')

        # Initialize filter expressions
        filter_expression = None

        # Build filter expressions for each specified query parameter
        if title:
            filter_expression = Key('title').eq(title)
        if description:
            if filter_expression:
                filter_expression &= Attr('description').contains(description)
            else:
                filter_expression = Attr('description').contains(description)
        if actors:
            if filter_expression:
                filter_expression &= Attr('actors').contains(actors)
            else:
                filter_expression = Attr('actors').contains(actors)
        if director:
            if filter_expression:
                filter_expression &= Attr('director').contains(director)
            else:
                filter_expression = Attr('director').contains(director)
        if genre:
            if filter_expression:
                filter_expression &= Attr('genre').contains(genre)
            else:
                filter_expression = Attr('genre').contains(genre)

        # Perform query using the Global Secondary Index (GSI) for Title if title is provided
        if title:
            response = table.query(
                IndexName='TitleIndex',  # Use the GSI name for querying
                KeyConditionExpression=Key('title').eq(title)
            )
        else:
            # If no title is specified, use scan with the constructed filter expression
            if filter_expression:
                response = table.scan(FilterExpression=filter_expression)
            else:
                response = table.scan()

        items = response.get('Items', [])

        return {
            'statusCode': 200,
            'body': json.dumps(items, cls=DecimalEncoder),
            'headers': headers
        }

    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }
