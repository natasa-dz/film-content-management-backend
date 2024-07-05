import json
import os
import boto3
import subprocess
import logging

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',  
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps('CORS preflight check passed')
        }
    logger.info(f"Received event: {event}")

    
    try:
        
        bucket = os.environ['CONTENT_BUCKET'] 
        key = event['body']['filename'] 
        resolutions = event['body']['resolutions']  
        film_id = event['body']['film_id']  


        # Download the original file
        input_file = f"/tmp/{os.path.basename(key)}"
        s3.download_file(bucket, key, input_file)

        # Transcode to different resolutions
        for resolution in resolutions:
            width = resolution.split('p')[0]
            output_key = f"{film_id}_{resolution}.mp4"  # Use film_id in the output key
            output_file = f"/tmp/{film_id}_{resolution}.mp4"


            subprocess.run(['ffmpeg', '-i', input_file, '-vf', f"scale={width}:-1", output_file], check=True)

            # Upload transcoded file back to S3
            s3.upload_file(output_file, bucket, output_key)
            logger.info(f"Uploaded {resolution} version to S3: {bucket}/{output_key}")

    except Exception as e:
        logger.error(f"Error transcoding or uploading: {e}")
        raise

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Transcoding and upload successful'}),
        'headers': headers
    }
