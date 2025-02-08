import jwt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def permission_handler(event, context):
    print(event)
    print(event['authorizationToken'])
    try:
        token = event['authorizationToken'].split(" ")[1]
        print(token)
        jwt_decode = jwt.decode(token, options={"verify_signature": False})
        print(jwt_decode)
        principal_id = jwt_decode['sub']
        user_groups = jwt_decode.get('cognito:groups', [])
        method_arn = event['methodArn']

        if 'user' in [group.lower() for group in user_groups]:
            effect = 'Allow'
        else:
            effect = 'Deny'


        return {
            'principalId': principal_id,
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': method_arn
                }]
            }
        }

    except Exception as e:
        return {
            'principalId': 'admin',
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Deny',
                    'Resource': event['methodArn']
                }]
            }
        }
