import json
import boto3
import os
from decimal import Decimal

# Initialize the DynamoDB resource and table name
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['METADATA_TABLE']

def handler(event, context):
    # Access the table
    table = dynamodb.Table(table_name)
    
    # Parse the input from the event
    body = json.loads(event['body'])
    film_id = body['film_id']
    metadata = body.get('metadata', {})
    
    if not metadata:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No metadata provided for update'})
        }
    
    # Construct the update expression and attribute values
    update_expression = "SET "
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    for key, value in metadata.items():
        # Use expression attribute names to handle reserved keywords
        expression_attribute_names[f"#{key}"] = key
        update_expression += f"#{key} = :{key}, "
        expression_attribute_values[f":{key}"] = value

    update_expression = update_expression.rstrip(", ")

    # Update the item in DynamoDB
    try:
        response = table.update_item(
            Key={'film_id': film_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="UPDATED_NEW"
        )
        updated_attributes = response.get('Attributes', {})

        # Convert Decimal to float for JSON serialization
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Metadata updated successfully',
                'updated_attributes': updated_attributes
            }, default=decimal_default)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
