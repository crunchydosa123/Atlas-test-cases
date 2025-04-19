#app.py

from flask import Flask, request, abort
import os
import hmac
import hashlib
import requests
from github_app import get_installation_access_token, push_test_cases
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

def verify_signature(payload, signature):
    sha_name, signature = signature.split('=')
    mac = hmac.new(WEBHOOK_SECRET.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(payload, sig):
        abort(403)

    event = request.headers.get("X-GitHub-Event")
    json_payload = request.json

    if event == "push":
        repo_full_name = json_payload["repository"]["full_name"]
        installation_id = json_payload["installation"]["id"]

        # 🔁 Fetch test cases from your external API
        test_case_response = requests.get(f"https://your-api.com/testcases?repo={repo_full_name}")
        test_cases = test_case_response.text

        # 🔐 Get token & push
        token = get_installation_access_token(installation_id)
        push_test_cases(token, repo_full_name, test_cases)

    return "", 200