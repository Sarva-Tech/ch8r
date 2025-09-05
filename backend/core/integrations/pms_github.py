import requests
import logging

PMS_GITHUB_TOOLS = {
    "list_github_issues": {
        "type": "function",
        "function": {
            "name": "list_github_issues",
            "description": (
                "Call this function when the user asks about a feature, bug, or request. "
                "Search GitHub issues using `query` for accurate matches."
                "The repository is automatically determined from the integration and does not need to be specified."
                "Provide the most meaningful content from the issues, such as the title, state, and summary of the issue. "
                "Do **not** include the GitHub URL or any direct link to the issue. "
                "If no results are found, ask the user for more specific keywords."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keyword or phrase describing the feature, bug, or request the user is asking about. Example: 'bulk import', 'backup failure'.",
                    }
                },
                "required": ["query"]
            }
        }
    },
    "create_github_issue": {
        "type": "function",
        "function": {
            "name": "create_github_issue",
            "description": (
                "Call this function to create a new GitHub issue for a bug, feature request, or task. "
                "The repository is automatically determined from the integration and does not need to be specified."
                "You can automatically generate a suitable title and description based on the user's request, "
                "but **always ask the user for confirmation** before actually creating the issue. "
                "Always ask the user for confirmation before actually creating the issue."
                "**Do not share the GitHub URL**."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the GitHub issue. Example: 'Fix login bug', 'Add bulk import feature'."
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional detailed description of the issue."
                    }
                },
                "required": ["title"]
            }
        }
    }
}

logger = logging.getLogger(__name__)

def list_github_issues(app_integration, **kwargs):
    logger.info("Listing GitHub issues...")
    query = kwargs.get("query", "").strip()

    token = app_integration.integration.config["token"]
    repo = app_integration.metadata.get("branch_name")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    query_parts = [f"repo:{repo}", "is:issue"]

    if query:
        query_parts.append(query)

    full_query = " ".join(query_parts)

    url = "https://api.github.com/search/issues"
    resp = requests.get(url, headers=headers, params={"q": full_query})
    resp.raise_for_status()

    return {
        "repo": repo,
        "issues": [
            {
                "title": item["title"],
                "url": item["html_url"],
                "state": item["state"],
            }
            for item in resp.json().get("items", [])
            if "pull_request" not in item
        ]
    }

def create_github_issue(app_integration, **kwargs):
    logger.info("Creating GitHub issue...")
    title = kwargs.get("title", "").strip()
    description = kwargs.get("description", "").strip()

    if not title:
        raise ValueError("title is required to create a GitHub issue")

    token = app_integration.integration.config["token"]
    repo = app_integration.metadata.get("branch_name")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    url = f"https://api.github.com/repos/{repo}/issues"

    payload = {
        "title": title,
    }
    if description:
        payload["body"] = description

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()

    issue_data = resp.json()
    return {
        "repo": repo,
        "issue": {
            "title": issue_data["title"],
            "url": issue_data["html_url"],
            "state": issue_data["state"],
            "number": issue_data["number"]
        }
    }

PMS_GITHUB_HANDLERS = {
    "list_github_issues": list_github_issues,
    "create_github_issue": create_github_issue
}

