import json
import boto3
import os
import logging
import time


logger = logging.getLogger()
logger.setLevel(logging.INFO)
sfn_client = boto3.client('stepfunctions')

def handler(event, context):

    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    # if event['httpMethod'] == 'OPTIONS':
    #     return {
    #         'statusCode': 200,
    #         'headers': headers,
    #         'body': json.dumps('CORS preflight check passed')
    #     }
    
    logger.info(f"Received event: {event}")
    
      # Process each record in the SQS message
    for record in event['Records']:
        logger.info("FOR ZA RECORDS SQSA POKRENUT")
        # Extract the message body
        message_body = json.loads(record['body'])

        film_id = message_body['film_id']


    state_machine_arn = os.environ['STATE_MACHINE_ARN']
    logger.info(f"STATE_MACHINE_ARN: {state_machine_arn}")
    # film_id = event['pathParameters']['film_id']
    # logger.info(f"FILM_ID: {film_id}")
    
    try:
        logger.info("STARTING STEP FUNCTION EXECUTION")
        response = sfn_client.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps({
                "film_id": film_id
            })
        )
        execution_arn = response['executionArn']

        logger.info(f"execution arn that returns: {execution_arn}")
            
            
        return {
            'statusCode': 200,
            "headers": headers,
            'body': json.dumps({
                'message': 'Step Function execution started',
                'executionArn': execution_arn
            })
        }
    except Exception as e:
        logger.error(f"Error on starting of step function: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error starting Step Function execution',
                'error': str(e)
            })
        }