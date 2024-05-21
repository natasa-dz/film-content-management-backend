import json
import boto3
import os
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    
    # S3 bucket and DynamoDB table names
    bucket = os.environ['CONTENT_BUCKET']
    table_name = os.environ['METADATA_TABLE']
    table = dynamodb.Table(table_name)

    # Get the object from the event
    for record in event['Records']:
        key = record['s3']['object']['key']
        response = s3.head_object(Bucket=bucket, Key=key)
        
        # Extract metadata
        file_metadata = {
            'file_name': key,
            'file_type': key.split('.')[-1],
            'file_size': response['ContentLength'],
            'creation_time': response['LastModified'].isoformat(),
            'last_modified_time': response['LastModified'].isoformat()
        }
        
        # Generate a unique film ID (you can use a better unique identifier strategy)
        film_id = key.split('/')[-1].split('.')[0]
        
        # Add additional metadata (this can be extended to take more input)
        additional_metadata = {
            'title': key.split('/')[-1],
            'description': '',
            'actors': [],
            'directors': [],
            'genres': []
        }
        
        # Combine metadata
        metadata = {**file_metadata, **additional_metadata}
        
        # Store metadata in DynamoDB
        table.put_item(Item={'film_id': film_id, **metadata})
        
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'File metadata stored successfully'})
    }
