import json
import boto3
import os

dynamodb=boto3.resource('dynamodb')

def handler(event, context):
    table_name = os.environ['TABLE_NAME']
    table = dynamodb.Table(table_name)

    film_id=event['queryStringParameters'].get('film_id') if event['queryStringParameteres'] else None

    if film_id:

        # Get specific film metadata
        response = table.get_item(Key={'film_id': film_id})
        item = response.get('Item', {})
        return {
            'statusCode': 200,
            'body': json.dumps(item)
        }
    
    else:
        response = table.scan()
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'])
        }