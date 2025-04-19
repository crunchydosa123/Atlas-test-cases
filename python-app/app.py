import time
import jwt
import requests
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

# GitHub App info
GITHUB_APP_ID = '1221676'  # Your GitHub App ID
GITHUB_PRIVATE_KEY = '''-----BEGIN RSA PRIVATE KEY-----
MIIEpgIBAAKCAQEAuFHLuLLzWCua5ZVqpo5CQFfv75S/jc8/Z5tqX26AscaAn5nN
janGr5Pwu54AJZSNgQ2fZWiunDl+Q2JOTY4tr+suJaPDB11fy/CqpWmb76mAEPLH
mgH61jgLFQKVmcrIOnhCgP4GHQzmSBPo6hJU66dWabHi2C0d/99TGL/Kd/v6qQ/q
rvYlloGSpUGBGkOHH0U7jcOsQQdPa18oWgSbznrLbUAAkevS4U+KUOCznVfdSNpG
+aw+9nGnDopVE2YRNOn0xrmRCgltfEmiEO5h/8dpr8myDItwV8mhKU3pyqijlPHV
shRvtW1d0/KHBWlHsHn5kfIp0EvGtufjyvbjDwIDAQABAoIBAQCi3+TduYQ/jYi7
B2XO+DajFRH468C5V0H4E+XTnpoqffZ7EjYJ0NS5oklAAUav7q18NMV9nxttAYEJ
mn0HG3RT18ZXjHZys5hLZsfkk4YwKd/5GhA3jzhQxAVG85mu5Po6cLqTseVFFnkH
iFBxRvGzq5M4ovCJhpTT3kxXumL30jfoUDD3kFronJuKUBnpMTaerS4f5iB+sKpO
IpG7P4jNSNxAVHY4UXzCsjcDs8I9XhDwt0/Kzv887mPI2CxHm3ic5/m4X3A8T4Ae
KTVR/n5PS2Az3cKMe/9JIyA3IeQulSlUABoEwBGzxfO4MtPE02il8QnTFDoq4Yxh
/QGvEiSBAoGBAPTx5tfRJnSSq/BNcm0XE42/OTxfop8PaR0pFYdzy7KirVecxHR8
C+KYROgA4y107tWzGM5yz3UYf3vm4ic3APJZl3eV+SlogIYwt/QzHUqE9jtiQl/Z
6cIRRN5qV/yjV81nfMysule66bj6dOmFNF0AHkVnmVM+QhgHRdgQMHXpAoGBAMCj
bUkCg2Z/rm63YbbJh7+XRMUpKMtlPohE/TUelkD+dWOl1Jmk41iyXC0E74dtDOn0
kMW3kGSsVzxYXv0GMkQg84ryC8xUwr1LCGF3UKX4mXMNxrxZwCXak7a2UpC+zyhA
lTCbbXHSTpCYG+wd0+OcMXrtornJwUumtxI38l43AoGBALzQqAjfQcyEr6Oqn7U2
H62ZpW5DrmD8iSOgYucqPPBz9DlgMBQ29xZyGFPbM0P8Koty5oFmAUObYdJJ9TUT
clhe9aKKaiogU0qdzX+h00d5XTIDmXS3zzj5BOSKh07JP0qoJozD7VTpUXd1IaBN
PUMfbzZDGO8RQ/Ovz4gxWpnZAoGBAJrwFwr82YDMOxjTp+TjbKp9WROWyjflY4ko
q9tYkZMO1o3iJ/+3rh99vUN8T8dFv3hAe1x7CsjeEH/5t9Sccjt3oUpk6XZbyhGD
0ubJl3UWYR03vFtreG85wUrYk8nVnjqKzzO8HyfH9ea4YOTlDLJpwyZTEWmKy0w0
d9RQaUC7AoGBAO7r6co99aJ87ZaquTiUzmKv5zpPBMGzLdotpVmKXNcY2MF7fWKv
Dn38bWwfF3Wdgu5huzV6GINk6G1eAn+YYAJd/RTrYF0klPdeXqqryvgQb1QU7gzU
RlXASR3w/qFmyNjgQIUzzZtU43kHzqcUqK8BFYHMLUSleP7Zjw2wZJoo
-----END RSA PRIVATE KEY-----'''  # Your GitHub App private key as a multi-line string
GITHUB_API_URL = "https://api.github.com"

@app.route('/github/callback')
def github_callback():
    installation_id = request.args.get('installation_id')
    if installation_id:
        print(f"🔁 Received installation ID from GitHub: {installation_id}")

        jwt_token = generate_jwt()
        access_token = get_installation_token(jwt_token, installation_id)

        if access_token:
            print("✅ Installation access token received.")

            # Step 1: Get the list of repositories for the installation
            repos = get_repositories(access_token)
            if not repos:
                return jsonify({"error": "No repositories found for this installation"}), 404

            # Step 2: Push test case to each repository
            file_path = "tests/test_case.js"
            commit_message = "Add AI-generated test case"
            test_case_content = generate_test_case()

            results = []
            for repo in repos:
                owner = repo['owner']['login']
                repo_name = repo['name']
                print(f"📁 Pushing to {owner}/{repo_name}")
                response = push_test_case_to_repo(access_token, owner, repo_name, file_path, commit_message, test_case_content)

                if response.status_code == 201:
                    results.append(f"Test case pushed to {owner}/{repo_name} successfully!")
                else:
                    results.append(f"Failed to push test case to {owner}/{repo_name}: {response.json()}")

            return jsonify({"message": "Test case push results", "results": results})

        else:
            return "Failed to get access token", 400

    else:
        return "No installation ID found. Did something go wrong?", 400

def generate_jwt():
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
        "iss": GITHUB_APP_ID
    }
    return jwt.encode(payload, GITHUB_PRIVATE_KEY, algorithm="RS256")

def get_installation_token(jwt_token, installation_id):
    url = f"{GITHUB_API_URL}/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(url, headers=headers)
    return response.json().get('token') if response.status_code == 201 else None

def get_repositories(access_token):
    url = f"{GITHUB_API_URL}/installation/repositories"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('repositories', [])
    else:
        print("❌ Failed to get repositories:", response.json())
        return []

def push_test_case_to_repo(access_token, owner, repo, path, message, content):
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{path}"
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    payload = {
        "message": message,
        "content": encoded_content
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    return requests.put(url, json=payload, headers=headers)

def generate_test_case():
    return """
    describe('Example Test Case', () => {
        it('should do something', () => {
            expect(true).toBe(true);
        });
    });
    """

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
