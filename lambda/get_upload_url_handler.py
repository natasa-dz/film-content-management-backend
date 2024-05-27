import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
bucket_name = os.environ.get('CONTENT_BUCKET')


def handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    
    def generate_presigned_url(object_key, expires_in):
        try:
            response = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expires_in,
                HttpMethod='PUT'
            )
            logger.info("Got presigned PUT URL: %s", response)
        except ClientError:
            logger.exception(
                "Couldn't get a presigned PUT URL for bucket '%s' and object '%s'",
                bucket_name,
                object_key,
                str(e)
            )
            raise
        return response

    try:
        film_id = event['queryStringParameters'].get('film_id')
        file_name = event['queryStringParameters'].get('file_name')

        if not film_id or not file_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'film_id and file_name are required'}),
                'headers': headers
            }

        s3_key = f"{film_id}-{file_name}"

        presigned_url = generate_presigned_url(s3_key, 3600)

        return {
            'statusCode': 200,
            'body': json.dumps({'upload_url': presigned_url}),
            'headers': headers
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }
