import pandas as pd
import gitlab
import json
from botocore.exceptions import ClientError

api = gitlab.Gitlab.from_config(config_files=['gitlab-conf.cfg']) #load gitlab server's details and credentials from a file

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        sheet_id = body.get('sheet_id')

        if not sheet_id:
            return error_response("Missing 'sheet_id' in request body.")

        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(csv_url)
        except Exception as e:
            return error_response(f"Error reading the CSV from Google Sheets: {str(e)}")

        new_users = add_user(api, df)
        create_repositories(api, new_users)

        return success_response("Successfully processed users and repositories.")

    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(f"Error: {str(e)}")

def add_user(api, df):
    new_users = []
    for _, row in df.iterrows():
        try:
            user = api.users.create({
                'username': row['username'],
                'name': row['name'],
                'email': row['email'],
                'skip_confirmation': True,
                'reset_password': True
            })
            print(f"User {user.username} created.")
            new_users.append(user)
        except gitlab.exceptions.GitlabCreateError as e:
            print(f"Error creating user {row['username']}: {str(e)}")
    return new_users

def create_repositories(api, new_users):
    for user in new_users:
        try:
            api.projects.create({'name': user.username})
            print(f"Project created for {user.username}.")
        except gitlab.exceptions.GitlabCreateError as e:
            print(f"Error creating project for {user.username}: {str(e)}")

def success_response(message):
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
    return {
        'statusCode': 500,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({"error": message})
    }
