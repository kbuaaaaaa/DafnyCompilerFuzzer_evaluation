import boto3
from botocore.exceptions import ClientError
import json
import requests


def get_secret():

    secret_name = "github_gatherer_pat"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = json.loads(get_secret_value_response['SecretString'])["GATHERER_PAT"]
    return secret

def get_test_program():
    with open('/tmp/reduced.dfy', 'r') as file:
        test_program = file.read()
    return test_program

def get_command_output():
    with open('/tmp/reduced_fuzz-d.log', 'r') as file:
        output = file.read()
    return output

def file_github_issue(first_bad_commit, language, behaviour, command, output):
    # GitHub repository information
    repo_owner = "kbuaaaaaa"
    repo_name = "dafny"

    # GitHub API endpoint for creating an issue
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"

    # Issue title and body
    issue_title = f"{behaviour} for {language}"
    issue_body = "## Dafny Version\nCommit "+ first_bad_commit +"\n## Code to produce this issue\n```dafny\n"+ get_test_program() + "```\n## Command to Run and Resulting Output\n```\n" + command +"```\n\n```\n"+ output +"```\n## What type of operating system are you experiencing the problem on?\nLinux"

    # GitHub personal access token for authentication
    access_token = get_secret()

    # Request headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.raw+json"
    }

    # Request payload
    payload = {
        "title": issue_title,
        "body": issue_body
    }

    # Send POST request to create the issue
    response = requests.post(url, headers=headers, json=payload)

    # Check if the request was successful
    if response.status_code == 201:
        return {
        'statusCode': 200,
        'body': json.dumps('Processing complete: bug processed and issued')
        }
    else:
        print("Failed to create issue")
        return {
            'statusCode': response.status_code,
            'body': response.content
        }

def comment_on_pr(first_bad_commit, language, behaviour, command, output, location):
    owner = 'dafny-lang'
    repo = 'dafny'
    branch = location

    response = requests.get(
        f'https://api.github.com/repos/{owner}/{repo}/pulls',
        headers={'Accept': 'application/vnd.github.v3+json'},
        params={'head': f'{owner}:{branch}', 'base': 'master'}
    )

    pull_requests = response.json()
    for pr in pull_requests:
        # Comment on the PR
        comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr['number']}/comments"
        access_token = get_secret()

        # Request headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.raw+json"
        }

        comment_body = f"##{behaviour} for {language}\n##Dafny version\nCommit {first_bad_commit}\n## Code to produce this issue\n```dafny\n{get_test_program()}```\n## Command to Run and Resulting Output\n```\n{command}```\n\n```\n{output}```\n"
        comment_payload = {
            "body": comment_body
        }
        comment_response = requests.post(comment_url, headers=headers, json=comment_payload)
        if comment_response.status_code == 201:
            print("Comment posted successfully")
        else:
            print("Failed to post comment")

def lambda_handler(event, context):
    # Extract the bucket name and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    
    # Extract the folder name from the object key
    folder_name = '/'.join(object_key.split('/')[:-1]) + '/'
    
    # Log the bucket name, object key, and folder name
    print(f"Bucket: {bucket_name}")
    print(f"Object Key: {object_key}")
    print(f"Folder Name: {folder_name}")

    # Create an S3 client
    s3_client = boto3.client('s3')

    # Download the file from S3
    s3_client.download_file(bucket_name, folder_name + 'data.txt', '/tmp/data.txt')
    s3_client.download_file(bucket_name, folder_name + 'reduced.dfy', '/tmp/reduced.dfy')
    s3_client.download_file(bucket_name, folder_name + 'reduced_fuzz-d.log', '/tmp/reduced_fuzz-d.log')

    # Print a message indicating the file has been downloaded
    print(f"File downloaded from S3")
    
    # Extract information from data.txt
    with open('/tmp/data.txt', 'r') as file:
        lines = file.readlines()
        location = lines[0].split(': ')[1].strip()
        first_bad_commit = lines[1].split(': ')[1].strip()
        language = lines[2].split(': ')[1].strip()
        hashed_bug = lines[3].split(': ')[1].strip()
        issue_no = lines[4].split(': ')[1].strip()

    # Read the reduced fuzzd log
    with open('/tmp/reduced_fuzz-d.log', 'r') as file:
        output = file.read()
        output.split(r'(Behaviour|Command|Output):\n')
        behaviour = output[1]
        command = output[2]
        output = output[3]

    if issue_no == "None":
        if location == "master":
            file_github_issue(first_bad_commit, language, behaviour, command, output)
        else:
            comment_on_pr(first_bad_commit, language, behaviour, command, output, location)

    # Move the folder to the bugs/first_bad_commit/category directory
    new_folder_name = f'bugs/{location}/{hashed_bug}/'
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
    for obj in response['Contents']:
        old_key = obj['Key']
        new_key = old_key.replace(folder_name, new_folder_name)
        s3_client.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': old_key}, Key=new_key)
        s3_client.delete_object(Bucket=bucket_name, Key=old_key)

    print("Folder moved successfully")
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete: Folder moved successfully')
    }