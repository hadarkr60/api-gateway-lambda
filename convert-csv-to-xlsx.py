import boto3
import pandas as pd
from io import BytesIO

s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        parameter = event['queryStringParameters']['parameter']

        if not parameter.startswith('https://'):
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': 'Invalid S3 path. Make sure the URL is correct.'
            }

        bucket_name, key = extract_bucket_and_key(parameter)
        print(f"Bucket: {bucket_name}, Key: {key}")

        csv_obj = s3.get_object(Bucket=bucket_name, Key=key)
        csv_data = csv_obj['Body'].read().decode('utf-8')

        df = pd.read_csv(BytesIO(csv_data.encode('utf-8')))
        xlsx_buffer = BytesIO()
        df.to_excel(xlsx_buffer, index=False, header=True)

        new_key = key.replace('.csv', '.xlsx')
        s3.put_object(
            Bucket=bucket_name,
            Key=new_key,
            Body=xlsx_buffer.getvalue(),
            ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': f'File successfully converted and saved as {new_key}'
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': f'Error: {str(e)}'
        }

def extract_bucket_and_key(s3_url):
    """Extract bucket name and key from an S3 URL."""
    s3_url = s3_url.replace('https://', '', 1)
    parts = s3_url.split('/', 1)
    bucket_name = parts[0].split('.')[0]
    key = parts[1]
    return bucket_name, key
