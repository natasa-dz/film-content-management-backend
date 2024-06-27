import json
import boto3
import os
import logging
from decimal import Decimal
from botocore.exceptions import ClientError
import base64

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('METADATA_TABLE')
s3_client = boto3.client('s3')
bucket_name = os.environ.get('CONTENT_BUCKET')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
            response = table.get_item(Key={'film_id': film_id})
            item = response.get('Item', {})

            if not item:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Film not found'}),
                    'headers': headers
                }

            s3_key = f"{film_id}"

            try:
                response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
                file_content = response['Body'].read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                # Include the file content in the response
                item['file'] = file_base64

                return {
                    'statusCode': 200,
                    'body': json.dumps(item, default=decimal_default),
                    'headers': headers
                }
            except ClientError as e:
                logger.error(e)
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Error fetching file from S3'}),
                    'headers': headers
                }
        else:
            # Scan and get all film metadata
            response = table.scan()
            items = response['Items']

            return {
                'statusCode': 200,
                'body': json.dumps(items, default=decimal_default),
                'headers': headers
            }

    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }

        #Refactor the lambda function to retrieve the film information as well,
        # when downloading the metadata to get the info about the sizing and download size of the movie,
        # so its compleete and shown to the user when listing all the movies!

        # add the transcoding option so the movie can be
        # downloaded in different resolutions
        # use the transocding options
