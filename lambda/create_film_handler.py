import json
import os
import base64
import boto3

s3 = boto3.client('s3')
table_name = os.environ['METADATA_TABLE']
dynamodb = boto3.resource('dynamodb')
bucket_name = os.environ['CONTENT_BUCKET']

#TODO : RESI CUVANJE GLUMACA

def handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        film_id = body.get('film_id')
        title = body.get('title')
        director = body.get('director')
        year = body.get('year')
        #actors=body.get('actors')
        description=body.get('description')
        file_base64 = body.get('file')

        headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  # Or use 'http://localhost:4200'
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        }

        # Validate required fields
        if not (film_id and title and director and year and file_base64):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'}),
                'headers':headers
            }

        # Save film data to DynamoDB
        table = dynamodb.Table(table_name)
        table.put_item(Item={
            'film_id': film_id,
            'title': title,
            'director': director,
            'year': year,
            'description':description,
            # 'actors':actors
        })

        # Decode the file from base64 and upload to S3
        file_content = base64.b64decode(file_base64)
        s3.put_object(Bucket=bucket_name, Key=film_id, Body=file_content)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Film created successfully'}),
            'headers':headers
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
