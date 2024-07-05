import json
import os
import boto3
import subprocess
import logging

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"Received event: {event}")

    bucket = event['bucket']
    key = event['key']
    resolutions = event['resolutions']

    try:
        # Download the original file
        input_file = f"/tmp/{os.path.basename(key)}"
        s3.download_file(bucket, key, input_file)

        # Transcode to different resolutions
        for resolution in resolutions:
            width = resolution.split('p')[0]
            output_key = f"{key}_{resolution}.mp4"
            output_file = f"/tmp/{os.path.basename(key)}_{resolution}.mp4"

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
    }
