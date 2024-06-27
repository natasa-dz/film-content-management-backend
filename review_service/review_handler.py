import json
import boto3
import uuid
import time

dynamodb = boto3.resource('dynamodb')
review_table = dynamodb.Table('ReviewTable')
movie_table = dynamodb.Table('MovieTable')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        
        review_id = str(uuid.uuid4())
        user_id = body['user_id']
        film_id = body['film_id']
        rating_type = body['rating_type']
        rating = body['rating']
        comment = body.get('comment', "")
        
        # Validate rating
        if rating_type not in ["numeric", "like_dislike", "thumbs"]:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Invalid rating type'})
            }
        
        if rating_type == "numeric" and (rating < 1 or rating > 5):
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Numeric rating must be between 1 and 5'})
            }
        
        if rating_type == "like_dislike" and rating not in ["like", "dislike"]:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Like/Dislike rating must be either "like" or "dislike"'})
            }
        
        if rating_type == "thumbs" and rating not in ["up", "down"]:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Thumbs rating must be either "up" or "down"'})
            }
        
        # Check if film exists
        film_response = movie_table.get_item(Key={'film_id': film_id})
        if 'Item' not in film_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Film not found'})
            }
        
        # Insert review into ReviewTable
        review_table.put_item(
            Item={
                'review_id': review_id,
                'user_id': user_id,
                'film_id': film_id,
                'rating_type': rating_type,
                'rating': rating,
                'comment': comment,
                'timestamp': int(time.time())
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Review submitted successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }
