import requests


class GitHubToolkit:
    def __init__(self, config):
        self.token = config["token"]
        self.repo = config["repo"]

    def get_function_declarations(self):
        return [
            {
                "name": "list_github_issues",
                "description": "Search GitHub issues by keyword (e.g., feature name). Use `query` for accurate matches.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Keyword or phrase to search for in issue titles or descriptions (e.g., 'backups', 'bulk import')"
                        },
                    },
                    "required": ["query"]
                }
            }
        ]

    def run_tool(self, name, params):
        if name != "list_github_issues":
            raise ValueError(f"Unsupported tool: {name}")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        query_parts = [f"repo:{self.repo}", "is:issue"]

        if "query" in params and params["query"].strip():
            query_parts.append(params["query"].strip())

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
