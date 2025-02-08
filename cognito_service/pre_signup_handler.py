import boto3

def handler(event, context):
    # Automatically confirm the user
    event['response']['autoConfirmUser'] = True
    
    # Set email as verified
    event['response']['autoVerifyEmail'] = True
    
    return event
