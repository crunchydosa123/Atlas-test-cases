#github_app.py

import jwt
import time
import requests
from github import Github, GithubIntegration
import os

# Load env variables
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")

with open(GITHUB_PRIVATE_KEY_PATH, "r") as f:
    private_key = f.read()

def get_jwt():
    now = int(time.time())
    payload = {
        'iat': now,
        'exp': now + (10 * 60),
        'iss': GITHUB_APP_ID
    }
    return jwt.encode(payload, private_key, algorithm='RS256')

def get_installation_access_token(installation_id):
    jwt_token = get_jwt()

    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github+json'
    }

    url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
    r = requests.post(url, headers=headers)
    r.raise_for_status()

    return r.json()['token']

def push_test_cases(token, repo_full_name, test_cases):
    g = Github(token)
    repo = g.get_repo(repo_full_name)

    file_path = "testcases/generated_test_cases.txt"
    commit_msg = "Add generated test cases"
    content = test_cases

    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, commit_msg, content, contents.sha)
    except Exception:
        repo.create_file(file_path, commit_msg, content)