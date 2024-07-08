import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client('stepfunctions')

#nece se koristiti realno se moze ceo fajl obrisati al ajde....nek ostane za svaki slucaj
def handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps('CORS preflight check passed')
        }

    logger.info(f"Received event: {event}")

    execution_arn = event['pathParameters'].get('executionArn')
    if not execution_arn:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'message': 'Missing executionArn in query parameters'})
        }

    try:
        logger.info("starting description of execution")
        execution_status = client.describe_execution(executionArn=execution_arn)
        logger.info(f"ended description of execution, execution status obj is: {execution_status}")
        logger.info(f"returning status is: {execution_status['status']}")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'status': execution_status['status']})
        }
    except Exception as e:
        logger.error(f"Error describing execution: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'message': 'Error describing execution', 'error': str(e)})
        }
