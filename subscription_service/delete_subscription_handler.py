import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['SUBSCRIPTIONS_TABLE']
table = dynamodb.Table(table_name)

def handler(event, context):
    body = json.loads(event['body'])
    user_id = body['user_id']
    subscription_type = body['subscription_type']
    subscription_value = body['subscription_value']
    
    try:
        table.delete_item(
            Key={
                'user_id': user_id,
                'subscription_type': subscription_type
            },
            ConditionExpression="subscription_value = :val",
            ExpressionAttributeValues={":val": subscription_value}
        )
        response = {
            'statusCode': 200,
            'body': json.dumps({'message': 'Subscription deleted successfully'})
        }
    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    response['headers'] = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    return response
