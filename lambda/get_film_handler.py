import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('METADATA_TABLE')
s3 = boto3.client('s3')
bucket_name = os.environ.get('CONTENT_BUCKET')

def handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError

    try:
        table = dynamodb.Table(table_name)

        # Get the film_id from query string parameters if available
        film_id = event['queryStringParameters'].get('film_id') if event.get('queryStringParameters') else None

        if film_id:
            # Get specific film metadata
            response = table.get_item(Key={'film_id': film_id})
            item = response.get('Item', {})

            # Generate presigned URL for downloading the movie if s3_key exists
            if 's3_key' in item:
                presigned_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': item['s3_key']}, ExpiresIn=3600)
                item['download_url'] = presigned_url

            return {
                'statusCode': 200,
                'body': json.dumps(item, default=decimal_default),
                'headers': headers
            }
        else:
            # Scan and get all film metadata
            response = table.scan()
            items = response['Items']

            # Include presigned URLs for all items that have s3_key
            # for item in items:
            #     if 's3_key' in item:
            #         presigned_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': item['s3_key']}, ExpiresIn=3600)
            #         item['download_url'] = presigned_url

            return {
                'statusCode': 200,
                'body': json.dumps(items, default=decimal_default),
                'headers': headers
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }
