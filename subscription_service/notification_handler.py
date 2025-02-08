import json
import boto3
from boto3.dynamodb.conditions import Key
import os

dynamodb = boto3.resource('dynamodb')
subscriptions_table = dynamodb.Table(os.environ['SUBSCRIPTIONS_TABLE'])
sns = boto3.client('sns')
sns_topic_arn = os.environ['SNS_TOPIC_ARN']

def handler(event, context):
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_movie = record['dynamodb']['NewImage']
            film_id = new_movie['film_id']['S']
            title = new_movie['title']['S']
            director = new_movie['director']['S']
            actors = new_movie['actors']['L']
            genre = new_movie['genre']['S']

            subscribers = set()

            # Get subscribers for director
            response = subscriptions_table.query(
                IndexName='subscription_type-subscription_value-index',
                KeyConditionExpression=Key('subscription_type').eq('director') & Key('subscription_value').eq(director)
            )
            for item in response['Items']:
                subscribers.add(item['user_id'])

            # Get subscribers for actors
            for actor in actors:
                response = subscriptions_table.query(
                    IndexName='subscription_type-subscription_value-index',
                    KeyConditionExpression=Key('subscription_type').eq('actor') & Key('subscription_value').eq(actor['S'])
                )
                for item in response['Items']:
                    subscribers.add(item['user_id'])

            # Get subscribers for genre
            response = subscriptions_table.query(
                IndexName='subscription_type-subscription_value-index',
                KeyConditionExpression=Key('subscription_type').eq('genre') & Key('subscription_value').eq(genre)
            )
            for item in response['Items']:
                subscribers.add(item['user_id'])

            # Notify subscribers
            for subscriber in subscribers:
                email = get_email_by_username(subscriber)
                if email:
                    sns.publish(
                        TopicArn=sns_topic_arn,
                        Message=f'New film added: {title}',
                        Subject='New Film Notification'
                    )

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Notifications sent successfully'})
    }

def get_email_by_username(username):
    try:
        client = boto3.client('cognito-idp')
        user_pool_id = os.environ['USER_POOL_ID']
        response = client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        for attribute in response['UserAttributes']:
            if attribute['Name'] == 'email':
                return attribute['Value']
    except client.exceptions.UserNotFoundException:
        print(f"User {username} not found in Cognito.")
    except Exception as e:
        print(f"Error retrieving email for user {username}: {str(e)}")
    return None
