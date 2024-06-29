import json
import boto3
import os

def handler(event, context):
    client = boto3.client('cognito-idp')
    user_pool_id = os.environ['USER_POOL_ID']
    headers={
                'Access-Control-Allow-Origin': '*',  # Adjust as needed for production
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }
    try:
        username = event['queryStringParameters']['username']

        response = client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )

        # Find the custom role attribute
        user_role = 'User'  # Default to 'User' role if not found
        for attribute in response['UserAttributes']:
            if attribute['Name'] == 'custom:role':
                user_role = attribute['Value']
                break

        return {
            'statusCode': 200,
            'body': json.dumps({'role': user_role}),
            'headers': headers
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }
