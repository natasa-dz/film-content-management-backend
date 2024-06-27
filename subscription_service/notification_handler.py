import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
subscriptions_table = dynamodb.Table('SubscriptionsTable')
sns = boto3.client('sns')

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
                sns.publish(
                    TopicArn=f'arn:aws:sns:region:account-id:{subscriber}',
                    Message=f'New film added: {title}',
                    Subject='New Film Notification'
                )

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Notifications sent successfully'})
    }
