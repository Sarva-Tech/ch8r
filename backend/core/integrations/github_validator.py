import requests


def validate_github_token(credentials: dict) -> tuple[bool, str, dict]:
    token = credentials.get('token', '')
    if not token:
        return False, 'Token is required', {}
    try:
        resp = requests.get(
            'https://api.github.com/user',
            headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github+json',
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            account_metadata = {
                'login': data.get('login'),
                'name': data.get('name'),
                'avatar_url': data.get('avatar_url'),
                'html_url': data.get('html_url'),
            }
            return True, '', account_metadata
        return False, f'GitHub returned {resp.status_code}', {}
    except requests.RequestException as e:
        return False, str(e), {}
