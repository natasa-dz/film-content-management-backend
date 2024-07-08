import json
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
user_feed_table = dynamodb.Table(os.environ['USER_FEED_TABLE'])


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def handler(event, context):
    user_id = event['queryStringParameters']['user_id']

    try:
        # Query the user feed table to get the feed for the user
        response = user_feed_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        feed_items = response.get('Items', [])

        return {
            'statusCode': 200,
            'body': json.dumps(feed_items, default=decimal_default), 
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization'
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization'
            }
        }
