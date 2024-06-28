import json
import os
import base64
import boto3
import logging

s3 = boto3.client('s3')
table_name = os.environ['METADATA_TABLE']
dynamodb = boto3.resource('dynamodb')
bucket_name = os.environ['CONTENT_BUCKET']
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#TODO : RESI CUVANJE GLUMACA

def handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        film_id = body.get('film_id')
        title = body.get('title')
        director = body.get('director')
        year = body.get('year')
        actors=body.get('actors')
        description=body.get('description')
        genre=body.get('genre')
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
            'actors':actors,
            'genre':genre
        })

# Decode the file from base64
        try:
            file_content = base64.b64decode(file_base64)
        except Exception as e:
            logger.error(f"Error decoding base64 file: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid base64 file content'}),
                'headers': headers
            }

        # Validate decoded content
        if not file_content:
            logger.error('Decoded file content is empty')
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Decoded file content is empty'}),
                'headers': headers
            }

        # Upload file to S3
        try:
            s3.put_object(Bucket=bucket_name, Key=film_id, Body=file_content)
            logger.info(f"File for film_id {film_id} uploaded successfully to S3 bucket {bucket_name}")
        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Error uploading file to S3'}),
                'headers': headers
            }

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
