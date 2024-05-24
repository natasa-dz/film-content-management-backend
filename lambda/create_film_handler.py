import json
import os
from datetime import datetime
import boto3

s3 = boto3.client('s3')
table_name=os.environ['METADATA_TABLE']
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        film_id = body.get('film_id')
        title = body.get('title')
        director = body.get('director')
        year = body.get('year')

        # Validate required fields
        if not (film_id and title and director and year):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        # Save film data to DynamoDB
        
        table = dynamodb.Table(table_name)
        table.put_item(Item={
            'film_id': film_id,
            'title': title,
            'director': director,
            'year': year
        })

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Film created successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
