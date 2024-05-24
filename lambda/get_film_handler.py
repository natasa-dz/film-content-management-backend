import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['METADATA_TABLE']

def handler(event, context):
    table = dynamodb.Table(table_name)

    # Get the film_id from query string parameters if available
    film_id = event['queryStringParameters'].get('film_id') if event.get('queryStringParameters') else None

    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError

    if film_id:
        # Get specific film metadata
        response = table.get_item(Key={'film_id': film_id})
        item = response.get('Item', {})
        return {
            'statusCode': 200,
            'body': json.dumps(item, default=decimal_default),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    else:
        # Scan and get all film metadata
        response = table.scan()
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'], default=decimal_default),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
