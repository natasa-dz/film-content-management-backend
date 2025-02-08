import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from decimal import Decimal

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('METADATA_TABLE')
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

def format_movie_data(query_params):
    # Split actors by comma and strip spaces
    actors = query_params.get('actors', '')
    formatted_actors = ', '.join(actor.strip() for actor in actors.split(','))

    formatted_data = (
        f"title: {query_params.get('title', '')} | "
        f"director: {query_params.get('director', '')} | "
        f"description: {query_params.get('description', '')} | "
        f"genre: {query_params.get('genre', '')} | "
        f"actors: {formatted_actors}"
    )
    return formatted_data.lower()

def handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  # Allow all origins
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    try:
        query_params = event.get('queryStringParameters', {})
        film_type_string = format_movie_data(query_params)

        response = table.query(
            IndexName='FilmTypeIndex',
            KeyConditionExpression=Key('film_type').eq(film_type_string),
        )

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
