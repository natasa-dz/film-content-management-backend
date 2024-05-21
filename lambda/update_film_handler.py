import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    table_name = os.environ['METADATA_TABLE']
    table = dynamodb.Table(table_name)
    
    # Parse the input from the event
    body = json.loads(event['body'])
    film_id = body['film_id']
    update_expression = "SET "
    expression_attribute_values = {}
    
    for key, value in body['metadata'].items():
        update_expression += f"{key} = :{key}, "
        expression_attribute_values[f":{key}"] = value

    update_expression = update_expression.rstrip(", ")

    # Update the item in DynamoDB
    table.update_item(
        Key={'film_id': film_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Metadata updated successfully'})
    }
