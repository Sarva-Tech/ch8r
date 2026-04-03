import json
import logging
import requests

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }

def _creds(app_integration) -> tuple[str, str]:
    credentials = json.loads(app_integration.integration.credentials)
    token = credentials["token"]
    repo = (app_integration.metadata or {}).get("repo", "")
    return token, repo

def _gh_request(method: str, url: str, *, headers: dict, params: dict = None, json: dict = None, timeout: int = 15) -> requests.Response:
    logger.info("[github_api] %s %s | params=%s", method.upper(), url, params or {})
    resp = requests.request(method, url, headers=headers, params=params, json=json, timeout=timeout)
    logger.info("[github_api] %s %s | status=%d content_length=%s",
                method.upper(), url, resp.status_code, resp.headers.get("content-length", "?"))
    resp.raise_for_status()
    return resp

def list_commits(app_integration, **kwargs):
    token, repo = _creds(app_integration)
    params = {k: v for k, v in kwargs.items() if v is not None and k in
              ("sha", "path", "author", "since", "until", "per_page", "page")}
    resp = _gh_request("get", f"{GITHUB_API}/repos/{repo}/commits", headers=_headers(token), params=params)
    return [{"sha": c["sha"][:7], "message": c["commit"]["message"].splitlines()[0],
             "author": c["commit"]["author"]["name"], "date": c["commit"]["author"]["date"]}
            for c in resp.json()]

def list_pull_requests(app_integration, **kwargs):
    token, repo = _creds(app_integration)
    params = {k: v for k, v in kwargs.items() if v is not None and k in
              ("state", "head", "base", "sort", "direction", "per_page", "page")}
    params.setdefault("state", "open")
    resp = _gh_request("get", f"{GITHUB_API}/repos/{repo}/pulls", headers=_headers(token), params=params)
    return [{"number": pr["number"], "title": pr["title"], "state": pr["state"],
             "author": pr["user"]["login"], "created_at": pr["created_at"]}
            for pr in resp.json()]

def list_releases(app_integration, **kwargs):
    token, repo = _creds(app_integration)
    params = {k: v for k, v in kwargs.items() if v is not None and k in ("per_page", "page")}
    resp = _gh_request("get", f"{GITHUB_API}/repos/{repo}/releases", headers=_headers(token), params=params)
    return [{"tag": r["tag_name"], "name": r["name"], "draft": r["draft"],
             "prerelease": r["prerelease"], "published_at": r["published_at"]}
            for r in resp.json()]

def list_tickets(app_integration, **kwargs):
    token, repo = _creds(app_integration)
    params = {k: v for k, v in kwargs.items() if v is not None and k in
              ("state", "labels", "assignee", "sort", "direction", "since", "per_page", "page")}
    params.setdefault("state", "open")
    resp = _gh_request("get", f"{GITHUB_API}/repos/{repo}/issues", headers=_headers(token), params=params)
    return [{"number": i["number"], "title": i["title"], "state": i["state"],
             "labels": [l["name"] for l in i["labels"]], "created_at": i["created_at"]}
            for i in resp.json() if "pull_request" not in i]


def create_ticket(app_integration, **kwargs):
    token, repo = _creds(app_integration)
    payload = {"title": kwargs["title"]}
    for field in ("body", "assignees", "milestone", "labels"):
        if kwargs.get(field) is not None:
            payload[field] = kwargs[field]
    resp = _gh_request("post", f"{GITHUB_API}/repos/{repo}/issues", headers=_headers(token), json=payload)
    d = resp.json()
    return {"number": d["number"], "title": d["title"], "state": d["state"]}


def get_ticket(app_integration, **kwargs):
    token, repo = _creds(app_integration)
    issue_number = kwargs["issue_number"]
    resp = _gh_request("get", f"{GITHUB_API}/repos/{repo}/issues/{issue_number}", headers=_headers(token))
    d = resp.json()
    return {"number": d["number"], "title": d["title"], "state": d["state"],
            "body": d.get("body", ""), "labels": [l["name"] for l in d["labels"]],
            "assignees": [a["login"] for a in d["assignees"]]}


def update_ticket(app_integration, **kwargs):
    token, repo = _creds(app_integration)
    issue_number = kwargs.pop("issue_number")
    payload = {k: v for k, v in kwargs.items() if v is not None and k in
               ("title", "body", "state", "assignees", "milestone", "labels")}
    resp = _gh_request("patch", f"{GITHUB_API}/repos/{repo}/issues/{issue_number}", headers=_headers(token), json=payload)
    d = resp.json()
    return {"number": d["number"], "title": d["title"], "state": d["state"]}


def lock_ticket(app_integration, **kwargs):
    token, repo = _creds(app_integration)
    issue_number = kwargs["issue_number"]
    payload = {}
    if kwargs.get("lock_reason"):
        payload["lock_reason"] = kwargs["lock_reason"]
    resp = _gh_request("put", f"{GITHUB_API}/repos/{repo}/issues/{issue_number}/lock", headers=_headers(token), json=payload)
    return {"locked": True, "issue_number": issue_number}


def unlock_ticket(app_integration, **kwargs):
    token, repo = _creds(app_integration)
    issue_number = kwargs["issue_number"]
    _gh_request("delete", f"{GITHUB_API}/repos/{repo}/issues/{issue_number}/lock", headers=_headers(token))
    return {"locked": False, "issue_number": issue_number}

GITHUB_VC_HANDLERS = {
    "list_commits": list_commits,
    "list_pull_requests": list_pull_requests,
    "list_releases": list_releases,
}

GITHUB_PM_HANDLERS = {
    "list_tickets": list_tickets,
    "create_ticket": create_ticket,
    "get_ticket": get_ticket,
    "update_ticket": update_ticket,
    "lock_ticket": lock_ticket,
    "unlock_ticket": unlock_ticket,
}
