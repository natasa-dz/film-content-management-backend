import json
import boto3
import os
import logging
from botocore.exceptions import ClientError

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
        'Access-Control-Allow-Methods': 'OPTIONS,POST,DELETE',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    try:
        table = dynamodb.Table(table_name)

        # Get the film_id from the request body
        film_id = event['pathParameters']['film_id']

        if not film_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Film ID is required'}),
                'headers': headers
            }

        # Delete the film metadata from DynamoDB
        try:
            response = table.delete_item(
                Key={'film_id': film_id},
                ConditionExpression="attribute_exists(film_id)"
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Film not found'}),
                    'headers': headers
                }
            else:
                logger.error(e)
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Error deleting metadata from DynamoDB'}),
                    'headers': headers
                }

        # Delete the film content from S3
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=film_id)
        except ClientError as e:
            logger.error(e)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Error deleting file from S3'}),
                'headers': headers
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Film deleted successfully'}),
            'headers': headers
        }

    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }
