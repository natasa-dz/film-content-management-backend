import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['SUBSCRIPTIONS_TABLE']
table = dynamodb.Table(table_name)

def handler(event, context):
    user_id = event['queryStringParameters']['user_id']
    
    try:
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        subscriptions = response['Items']
        response = {
            'statusCode': 200,
            'body': json.dumps(subscriptions)
        }
    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    response['headers'] = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    return response
