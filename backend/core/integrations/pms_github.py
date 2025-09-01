import requests

PMS_GITHUB_TOOLS = {
    "list_github_issues": {
        "type": "function",
        "function": {
            "name": "list_github_issues",
            "description": "Call this function when the user asks about a feature, bug, or request. Search GitHub issues using `query` for accurate matches.",
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
            "description": "Call this function to create a new GitHub issue for a bug, feature request, or task. Provide a title and optional description for the issue.",
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


def list_github_issues(integration, **kwargs):
    query = kwargs.get("query", "").strip()

    headers = {
        "Authorization": f"Bearer {integration.config["token"]}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # TODO: should be integration.app_integration.metadata.repo
    repo = "Sarva-Tech/ch8r"
    query_parts = [f"repo:{repo}", "is:issue"]

    if query:
        query_parts.append(query)

    full_query = " ".join(query_parts)

    url = "https://api.github.com/search/issues"
    resp = requests.get(url, headers=headers, params={"q": full_query})
    resp.raise_for_status()

    return {
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

PMS_GITHUB_HANDLERS = {
    "list_github_issues": list_github_issues,
}

