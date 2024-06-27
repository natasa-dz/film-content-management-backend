import json
import boto3
import os

def handler(event, context):
    client = boto3.client('cognito-idp')
    user_pool_id = os.environ['USER_POOL_ID']
    user_pool_client_id = os.environ['USER_POOL_CLIENT_ID']

    
    try:
        if event['httpMethod'] == 'POST':
            body = json.loads(event['body'])
            if 'register' in event['path']:
                # Register the user
                response = client.sign_up(
                    ClientId=user_pool_client_id,
                    Username=body['username'],
                    Password=body['password'],
                    UserAttributes=[
                        {'Name': 'email', 'Value': body['email']},
                        {'Name': 'name', 'Value': body['firstName']},
                        {'Name': 'family_name', 'Value': body['lastName']},
                        {'Name': 'birthdate', 'Value': body['dateOfBirth']},
                    ],
                    ValidationData=[
                        {'Name': 'custom:confirmation_status', 'Value': 'auto_confirmed'}
                    ]
                )

                # Add the user to the appropriate group
                group_name = body.get('group', 'User')  # Default to 'User' group if not specified
                client.admin_add_user_to_group(
                    UserPoolId=user_pool_id,
                    Username=body['username'],
                    GroupName=group_name
                )

                return {
                    'statusCode': 200,
                    'body': json.dumps(response),
                    'headers': {
                    'Access-Control-Allow-Origin': '*',  # Adjust as needed for production
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
                    }
                }
            elif 'login' in event['path']:
                # Login the user
                response = client.initiate_auth(
                    ClientId=user_pool_client_id,
                    AuthFlow='USER_PASSWORD_AUTH',
                    AuthParameters={
                        'USERNAME': body['username'],
                        'PASSWORD': body['password']
                    }
                )
                return {
                    'statusCode': 200,
                    'body': json.dumps(response),
                    'headers': {
                    'Access-Control-Allow-Origin': '*',  # Adjust as needed for production
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
                    }
                }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                    'Access-Control-Allow-Origin': '*',  # Adjust as needed for production
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
            }
        }
