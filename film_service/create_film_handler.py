import json
import os
import base64
import boto3
import logging
import subprocess
from urllib.parse import unquote_plus


s3 = boto3.client('s3')
table_name = os.environ['METADATA_TABLE']
dynamodb = boto3.resource('dynamodb')
bucket_name = os.environ['CONTENT_BUCKET']
user_pool_id = os.environ['USER_POOL_ID']


#notifications
sns = boto3.client('sns')
sqs_client = boto3.client('sqs')
subscriptions_table_name = os.environ['SUBSCRIPTIONS_TABLE']
subscriptions_table = dynamodb.Table(subscriptions_table_name)
sns_topic_arn = os.environ['SNS_TOPIC_ARN']


logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

def get_email_by_username(username):
    try:
        response = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        for attribute in response['UserAttributes']:
            if attribute['Name'] == 'email':
                return attribute['Value']
    except cognito.exceptions.UserNotFoundException:
        logger.error(f"User {username} not found in Cognito.")
    except Exception as e:
        logger.error(f"Error retrieving email for user {username}: {str(e)}")
    return None

def handler(event, context):

    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  # Or use 'http://localhost:4200'
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }
    
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps('CORS preflight check')
        }

    try:
        # Parse request body
        body = json.loads(event['body'])
        film_id = body.get('film_id')
        title = body.get('title')
        director = body.get('director')
        year = body.get('year')
        actors = body.get('actors')
        description = body.get('description')
        genre = body.get('genre')
        file_base64 = body.get('file')

        # Validate required fields
        if not (film_id and title and director and year and file_base64):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'}),
                'headers': headers
            }

        # Save film data to DynamoDB
        table = dynamodb.Table(table_name)
        table.put_item(Item={
            'film_id': film_id,
            'title': title,
            'director': director,
            'year': year,
            'description': description,
            'actors': actors,
            'genre': genre
        })

        # Decode the file from base64
        try:
            file_content = base64.b64decode(file_base64)
        except Exception as e:
            logger.error(f"Error decoding base64 file: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid base64 file content'}),
                'headers': headers
            }

        # Validate decoded content
        if not file_content:
            logger.error('Decoded file content is empty')
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Decoded file content is empty'}),
                'headers': headers
            }

        # Upload file to S3
        try:
            s3.put_object(Bucket=bucket_name, Key=film_id, Body=file_content)
            logger.info(f"File for film_id {film_id} uploaded successfully to S3 bucket {bucket_name}")
            # Send message to SQS queue
            response = sqs_client.send_message(
                QueueUrl=os.environ['FILM_UPLOAD_QUEUE_URL'],
                MessageBody=json.dumps({
                    'film_id': film_id
                })
            )

        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Error uploading file to S3'}),
                'headers': headers
            }

        # Notify subscribers
        notify_subscribers(title, actors, director, genre, description, year)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Film created'}),
            'headers': headers
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': headers
        }
    

def notify_subscribers(title, actors, director, genre, description, year):
    try:
        # Get all subscriptions that match the film's genre, director, or actors
        actors_flat = [actor.strip() for actor in actors]

        # Scan subscriptions table for items matching genre, director, or actors
        matching_subscriptions = subscriptions_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('subscription_value').is_in([genre, director] + actors_flat)
        )['Items']

        for subscription in matching_subscriptions:
            username = subscription['user_id']
            email = get_email_by_username(username)
            if email:                
                sns.publish(
                    TopicArn=sns_topic_arn,
                    Subject="New Film Uploaded",
                    Message=(
                        f"A new film has been uploaded that matches your subscription:\n"
                        f"Title: {title}\n"
                        f"Director: {director}\n"
                        f"Year: {year}\n"
                        f"Genre: {genre}\n"
                        f"Description: {description}"
                    ),
                    MessageAttributes={
                        'email': {
                            'DataType': 'String',
                            'StringValue': email
                        }
                    }
                ) 
            else:
                logger.error(f"Could not retrieve email for user {username}")

        logger.info(f"Notifications sent for film title: {title}")
    except Exception as e:
        logger.error(f"Error notifying users: {str(e)}")
