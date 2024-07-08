import json
import os
import boto3
import subprocess
import logging
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


    logger.info(f"Received event: {event}")

    try:
        bucket = os.environ['CONTENT_BUCKET'] 
        logger.info(f"CONTENT_BUCKET: {bucket}")


        film_id = event.get('film_id')
        

        if not film_id:
            raise ValueError("Missing film_id in request body")

        # Download the original file
        input_file = f"/tmp/{os.path.basename(film_id)}"
        if not check_file_exists_tmp(input_file):
            logger.info(f"Downloading file from S3: {film_id}")
            s3.download_file(bucket, film_id, input_file)

        key_360 = f"{film_id}_360p.mp4"
        key_720 = f"{film_id}_720p.mp4"
        key_480 = f"{film_id}_480p.mp4"


        if not check_file_exists_s3(bucket, key_360):
            logger.info(f"Transcoding to 360p")
            transcode_and_upload(input_file, bucket, key_360, "640:360")

        if not check_file_exists_s3(bucket, key_720):
            logger.info(f"Transcoding to 720p")
            transcode_and_upload(input_file, bucket, key_720, "1280:720")

        if not check_file_exists_s3(bucket, key_480):
            logger.info(f"Transcoding to 480p")
            transcode_and_upload(input_file, bucket, key_480, "854:480")

    except Exception as e:
        logger.error(f"Error transcoding or uploading: {e}")
        raise e
    

#--------------------------GENERALNO RETURN IZ OVOG FAJLA NE RADI NISTA FRONTU ALI APSOLUTNO NE STIGNE DO NJEGA ON UOPSTE NIJE SUBSCRIBOVAN NA OVO, NAMA TREBA DA MI OVO VRATIMO ZA STEP FJU PA DA ONA OBAVESTI
# FRONT O CEMU TREBA DA GA OBAVESTI AL AJDE PRVO DA PRORADI TRANSCODING PA CU DA VIDIM STA DALJE
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps({'message': 'Transcoding and upload successful'}),
    #     'headers': headers
    # }


def transcode_and_upload(input_file, bucket, output_key, resolution_interval):
    output_path = f"/tmp/{output_key}"
    transcode_video(input_file, output_path, resolution_interval)
    logger.info(f"Uploading transcoded file to S3: {output_key}")
    try:
        s3.upload_file(output_path, bucket, output_key)
    except Exception as e:
        raise e

def transcode_video(input_path, output_path, resolution):
    # Ensure output path has correct extension

    ffmpeg_cmd = [
        '/opt/bin/ffmpeg', '-y',
        '-i', input_path,
        '-vf', f'scale={resolution}',
        '-preset', 'ultrafast',
        '-crf', '23', 
        '-c:a', 'copy',
        output_path
    ]

    try:
        logger.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

    except Exception as e:
        logger.error(f"Error in transcode_video(): {e}")
        logger.error(f"ffmpeg output: {e.stdout.decode('utf-8')}")
        logger.error(f"ffmpeg error: {e.stderr.decode('utf-8')}")
        raise e

def check_file_exists_s3(bucket_name, file_key):
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        return True
    except ClientError as e:
        return False
    
def check_file_exists_tmp(file_path):
    if os.path.exists(file_path):
        return True
    return False