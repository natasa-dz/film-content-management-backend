import json
import os
import base64
import boto3
import logging

s3 = boto3.client('s3')
table_name = os.environ['METADATA_TABLE']
dynamodb = boto3.resource('dynamodb')
bucket_name = os.environ['CONTENT_BUCKET']
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        film_id = body.get('film_id')
        title = body.get('title')
        director = body.get('director')
        year = body.get('year')
        actors = body.get('actors')
        description = body.get('description')
        file_base64 = body.get('file')

        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # Or use 'http://localhost:4200'
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,PATCH',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        }

        # Validate required fields
        if not (film_id and (title or director or year or actors or description or file_base64)):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'}),
                'headers': headers
            }

        # Update film data in DynamoDB
        table = dynamodb.Table(table_name)
        update_expression = "SET "
        expression_attribute_values = {}

        if title:
            update_expression += "#title = :title, "
            expression_attribute_values[':title'] = title
        if director:
            update_expression += "#director = :director, "
            expression_attribute_values[':director'] = director
        if year:
            update_expression += "#year = :year, "
            expression_attribute_values[':year'] = year
        if actors:
            update_expression += "#actors = :actors, "
            expression_attribute_values[':actors'] = actors
        if description:
            update_expression += "#description = :description, "
            expression_attribute_values[':description'] = description

        update_expression = update_expression.rstrip(", ")

        try:
            if update_expression != "SET ":  # Ensure at least one field to update
                table.update_item(
                    Key={'film_id': film_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values,
                    ExpressionAttributeNames={
                        "#title": "title",
                        "#director": "director",
                        "#year": "year",
                        "#actors": "actors",
                        "#description": "description"
                    },
                    ReturnValues="UPDATED_NEW"
                )
                logger.info(f"Film with ID {film_id} updated successfully")
            else:
                logger.warning(f"No fields provided to update for film ID {film_id}")

        except Exception as e:
            logger.error(f"Error updating film with ID {film_id}: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Error updating film'}),
                'headers': headers
            }

        # Handle file update if provided
        if file_base64:
            try:
                file_content = base64.b64decode(file_base64)
                s3.put_object(Bucket=bucket_name, Key=film_id, Body=file_content)
                logger.info(f"File for film ID {film_id} updated successfully in S3 bucket {bucket_name}")
            except Exception as e:
                logger.error(f"Error updating file for film ID {film_id} in S3: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Error updating file in S3'}),
                    'headers': headers
                }

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Film updated successfully'}),
            'headers': headers
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Unexpected error'}),
            'headers': headers
        }
