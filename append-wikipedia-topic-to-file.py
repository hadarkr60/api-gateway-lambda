import boto3
import wikipedia
import json
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

S3_FILE_URL = "<your-bucket>"  #replace with your bucket name

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        body = json.loads(event.get('body', '{}'))
        topic = body.get('topic')

        if not topic:
            return error_response("Missing 'topic' in request body.")

        bucket_name, key = extract_bucket_and_key(S3_FILE_URL)
        logger.info(f"Bucket: {bucket_name}, Key: {key}")

        try:
            wiki_summary = wikipedia.summary(topic)
        except wikipedia.exceptions.DisambiguationError as e:
            return error_response(f"Disambiguation Error: {str(e)}")
        except wikipedia.exceptions.PageError:
            return error_response(f"No Wikipedia page found for '{topic}'.")

        existing_content = read_existing_content(bucket_name, key)

        updated_content = f"{existing_content}\n\n{wiki_summary}"

        write_content_to_s3(bucket_name, key, updated_content)

        message = f'Successfully appended summary of "{topic}" to {key}.'
        logger.info(message)

        return success_response(message)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(f"Error: {str(e)}")

def extract_bucket_and_key(s3_url):
    """Extract bucket name and key from an S3 URL."""
    s3_url = s3_url.replace('https://', '', 1)
    parts = s3_url.split('/', 1)
    bucket_name = parts[0].split('.')[0]
    key = parts[1]
    return bucket_name, key

def read_existing_content(bucket_name, key):
    """Read existing content from the S3 file."""
    try:
        s3_object = s3.get_object(Bucket=bucket_name, Key=key)
        return s3_object['Body'].read().decode('utf-8')
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info(f"{key} not found. Creating a new file.")
            return ""
        else:
            raise

def write_content_to_s3(bucket_name, key, content):
    """Write content to an S3 bucket."""
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=content.encode('utf-8'),
        ContentType='text/plain'
    )

def success_response(message):
    """Return a success response with CORS headers."""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({"message": message})
    }

def error_response(message):
    """Return an error response with CORS headers."""
    return {
        'statusCode': 500,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({"error": message})
    }
