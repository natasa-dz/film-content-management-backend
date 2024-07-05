# Upload your custom runtime zip file to S3 (optional, if not already uploaded)
import boto3
import os

lambda_client = boto3.client('lambda')

s3_client = boto3.client('s3')
bucket_name = os.environ['CONTENT_BUCKET']

object_key = 'transcoding_service.zip'
s3_client.upload_file('transcoding_service.zip', bucket_name, object_key)

# Create Lambda Layer
response = lambda_client.publish_layer_version(
    LayerName='ffmpeg-layer',
    Content={
        'S3Bucket': bucket_name,
        'S3Key': object_key,
    },
    CompatibleRuntimes=[
        'python3.9',  # Replace with your Python runtime version
    ],
    Description='Lambda Layer with ffmpeg binary',
)
layer_version_arn = response['LayerVersionArn']
print(f"Created Lambda Layer Version ARN: {layer_version_arn}")