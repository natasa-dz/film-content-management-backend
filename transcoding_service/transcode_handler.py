import json
import os
import boto3
import subprocess
import logging

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# TODO: UPAMTI DA KADA DOBAVLJAS TRANSCODED FILM IZ S3 BUCKET-A, 
# ID TI NIJE SAMO FILM_ID, nego ti key izgleda ovako: 
# film123_720p.mp4 ili film123_360p.mp4 ili filma123_1080p.mp4
# DOK TI JE ID ORIGINALNE REZOLUCIJE film123.mp4, bez sufixa!!!!

def handler(event, context):
    headers = {
        'Content-Type': 'application/json',
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

        if isinstance(event['body'], str):
            event_body = json.loads(event['body'])
        else:
            event_body = event['body']

        film_id = event_body.get('film_id')
        resolutions = event_body.get('resolutions')

        if not film_id:
            raise ValueError("Missing film_id in request body")
 

        # Download the original file
        input_file = f"/tmp/{os.path.basename(film_id)}"
        s3.download_file(bucket, film_id, input_file)

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
