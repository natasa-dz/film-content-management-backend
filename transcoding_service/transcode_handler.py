import json
import os
import boto3
import subprocess
import logging
from retrying import retry
from botocore.exceptions import ClientError


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
        # resolutions = event_body.get('resolutions')

        if not film_id:
            raise ValueError("Missing film_id in request body")
 

        # Download the original file
        input_file = f"/tmp/{os.path.basename(film_id)}"
        s3.download_file(bucket, film_id, input_file)

        transcode_and_upload(input_file, bucket, "1080", film_id, "1920:1080")
        transcode_and_upload(input_file, bucket, "720", film_id, "1280:720")
        transcode_and_upload(input_file, bucket, "480", film_id, "854:480")

        # key_1080 = f"{film_id}_1080p.mp4"
        # path_1080 = f"/tmp/{film_id}_1080p.mp4"
        # transcode_video(input_file, path_1080,  '1920:1080')
        # s3.upload_file(path_1080, bucket, key_1080)

        # key_720 = f"{film_id}_720p.mp4"
        # path_720 = f"/tmp/{film_id}_720p.mp4"
        # transcode_video(input_file, path_720, '1280:720')
        # s3.upload_file(path_720, bucket, key_720)

        # key_480 = f"{film_id}_480p.mp4"
        # path_480 = f"/tmp/{film_id}_480p.mp4"
        # transcode_video(input_file, path_480, '854:480')
        # s3.upload_file(path_480, bucket, key_480)


        # # Transcode to different resolutions
        # for resolution in resolutions:
        #     width = resolution.split('p')[0]
        #     output_key = f"{film_id}_{resolution}.mp4"  # Use film_id in the output key
        #     output_file = f"/tmp/{film_id}_{resolution}.mp4"

        #     subprocess.run(['ffmpeg', '-i', input_file, '-vf', f"scale={width}:-1", output_file], check=True)

        #     # Upload transcoded file back to S3
        #     s3.upload_file(output_file, bucket, output_key)
        #     logger.info(f"Uploaded {resolution} version to S3: {bucket}/{output_key}")

    except Exception as e:
        logger.error(f"Error transcoding or uploading: {e}")
        logger.error(f"Transaction didnt succeed, reverting...")

        if check_file_exists(bucket, f"{film_id}_1080p.mp4"):
            s3.delete_object(Bucket=bucket, Key=f"{film_id}_1080p.mp4")

        if check_file_exists(bucket, f"{film_id}_720p.mp4"):
            s3.delete_object(Bucket=bucket, Key=f"{film_id}_720p.mp4")


        if check_file_exists(bucket, f"{film_id}_480p.mp4"):
            s3.delete_object(Bucket=bucket, Key=f"{film_id}_480p.mp4")

        logger.error(f"Revert successful")

        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error while transcoding files. Transaction has been reverted!'}),
            'headers': headers}

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Transcoding and upload successful'}),
        'headers': headers
    }


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_attempt_number=5)
def transcode_and_upload(input_file, bucket, resolution, film_id, resolution_interval):
    output_path = f"/tmp/{film_id}_{resolution}p.mp4"
    output_key = f"{film_id}_{resolution}p.mp4"
    transcode_video(input_file, output_path, resolution_interval)
    s3.upload_file(output_path, bucket, output_key)

def transcode_video(input_path, output_path, resolution):
    ffmpeg_cmd = [
        '/opt/bin/ffmpeg',
        '-i', input_path,
        '-vf', f'scale={resolution}',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-c:a', 'aac',
        '-b:a', '128k',
        output_path
    ]
    subprocess.run(ffmpeg_cmd, check=True)


def check_file_exists(bucket_name, file_key):
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        return True
    except ClientError as e:
            return False