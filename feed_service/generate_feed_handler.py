import boto3
import json
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key

import os

dynamodb = boto3.resource('dynamodb')
film_table = dynamodb.Table(os.environ['METADATA_TABLE'])
user_ratings_table = dynamodb.Table(os.environ['REVIEW_TABLE'])
user_subscriptions_table = dynamodb.Table(os.environ['SUBSCRIPTIONS_TABLE'])
user_feed_table = dynamodb.Table(os.environ['USER_FEED_TABLE'])  # Assuming you have set USER_FEED_TABLE in environment
user_downloads_table = dynamodb.Table(os.environ['USER_DOWNLOADS_TABLE'])

def get_user_ratings(user_id):
    response = user_ratings_table.scan(
        FilterExpression=Attr('user_id').eq(user_id)
    )
    return response.get('Items', [])

def get_user_subscriptions(user_id):
    response = user_subscriptions_table.query(
        KeyConditionExpression=Key('user_id').eq(user_id)
    )
    return response.get('Items', [])

def get_user_downloads(user_id):
    response = user_downloads_table.query(
        KeyConditionExpression=Key('user_id').eq(user_id)
    )
    return response.get('Items', [])


def calculate_score(film, user_ratings, user_subscriptions, user_downloads):
    score = 0

    # Add points for ratings
    for rating in user_ratings:
        if rating['film_id'] == film['film_id']:
            rating_type = rating.get('rating_type')
            rating_value = rating.get('rating')

            if rating_type == 'numeric':
                if rating_value > 2:  
                    score += rating_value * 2  
            elif rating_type == 'like_dislike':
                if rating_value.lower() == 'like':  
                    score += 5  # weight for like/dislike ratings
            elif rating_type == 'thumbs':
                if rating_value.lower() == 'up':  
                    score += 5  # weight for thumbs up/down ratings

    # Add points for subscriptions
    for subscription in user_subscriptions:
        if subscription['subscription_type'] == 'genre' and subscription['subscription_value'] in film['genre']:
            score += 5  # weight for genre subscription
        if subscription['subscription_type'] == 'director' and subscription['subscription_value'] == film['director']:
            score += 5  # weight for director subscription
        if subscription['subscription_type'] == 'actor' and subscription['subscription_value'] in film['actors']:
            score += 5  # weight for actor subscription

    # Add points for downloads
    for download in user_downloads:
        if download['film_id'] == film['film_id']:
            score += 3  # weight for downloads

    return score

def handler(event, context):
    user_id = event['queryStringParameters']['user_id']

    # Fetch user data
    user_ratings = get_user_ratings(user_id)
    user_subscriptions = get_user_subscriptions(user_id)
    user_downloads = get_user_downloads(user_id)

    # Fetch all films
    response = film_table.scan()
    films = response['Items']

    # Calculate scores for each film
    scored_films = []
    for film in films:
        score = calculate_score(film, user_ratings, user_subscriptions, user_downloads)
        if score > 0:
            scored_films.append({'film': film, 'score': score})

    # Sort films by score
    scored_films.sort(key=lambda x: x['score'], reverse=True)

    # Return top 10 films
    #feed = []
    for film in scored_films[:10]:
        film_info = {
            'film_id': film['film']['film_id'],
            'title': film['film']['title'],
            'director': film['film']['director'],
            'year': film['film']['year'],
            'description': film['film']['description'],
            'actors': film['film']['actors'],
            'genre': film['film']['genre'],
            'score': film['score']
        }
        #feed.append(film_info)
        
        # Update user feed table
        user_feed_table.put_item(Item={
            'user_id': user_id,
            'film_id': film_info['film_id'],
            'title': film_info['title'],
            'director': film_info['director'],
            'year': film_info['year'],
            'description': film_info['description'],
            'actors': film_info['actors'],
            'genre': film_info['genre'],
            'score': film_info['score']
        })


    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Feed updated successfully'}),
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        }
    }
