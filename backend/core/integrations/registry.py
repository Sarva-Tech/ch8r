from core.integrations.pms_github import (
    list_github_issues,
    create_github_issue,
    PMS_GITHUB_HANDLERS,
)
from core.integrations.github_tools import GITHUB_HANDLERS

INTEGRATION_TOOLS = {
    "github_version_control": {
        "list_commits": {
            "id": "list_commits",
            "title": "List Commits",
            "description": (
                "Retrieve a list of commits for a repository branch, "
                "optionally filtered by author, path, or date range."
            ),
            "schema": {
                "type": "function",
                "function": {
                    "name": "list_commits",
                    "description": (
                        "Retrieve a list of commits for a repository branch, "
                        "optionally filtered by author, path, or date range."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sha": {"type": "string", "description": "SHA or branch to start listing commits from."},
                            "path": {"type": "string", "description": "Only commits containing this file path will be returned."},
                            "author": {"type": "string", "description": "GitHub login or email address by which to filter by commit author."},
                            "since": {"type": "string", "description": "Only show results updated after this time (ISO 8601)."},
                            "until": {"type": "string", "description": "Only commits before this date will be returned (ISO 8601)."},
                            "per_page": {"type": "integer", "description": "The number of results per page (max 100)."},
                            "page": {"type": "integer", "description": "The page number of the results to fetch."},
                        },
                        "required": [],
                    },
                },
            },
        },
        "list_pull_requests": {
            "id": "list_pull_requests",
            "title": "List Pull Requests",
            "description": (
                "Retrieve open, closed, or all pull requests for a repository, "
                "with optional filters for head branch, base branch, and sort order."
            ),
            "schema": {
                "type": "function",
                "function": {
                    "name": "list_pull_requests",
                    "description": (
                        "Retrieve open, closed, or all pull requests for a repository, "
                        "with optional filters for head branch, base branch, and sort order."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {"type": "string", "enum": ["open", "closed", "all"], "description": "Filter pull requests by state. Default: open."},
                            "head": {"type": "string", "description": "Filter by head user or organization and branch name (user:ref-name)."},
                            "base": {"type": "string", "description": "Filter pulls by base branch name."},
                            "sort": {"type": "string", "enum": ["created", "updated", "popularity", "long-running"], "description": "What to sort results by."},
                            "direction": {"type": "string", "enum": ["asc", "desc"], "description": "The direction of the sort."},
                            "per_page": {"type": "integer", "description": "The number of results per page (max 100)."},
                            "page": {"type": "integer", "description": "The page number of the results to fetch."},
                        },
                        "required": [],
                    },
                },
            },
        },
        "list_releases": {
            "id": "list_releases",
            "title": "List Releases",
            "description": (
                "Retrieve published releases for a repository. "
                "Draft releases are only visible to users with push access."
            ),
            "schema": {
                "type": "function",
                "function": {
                    "name": "list_releases",
                    "description": (
                        "Retrieve published releases for a repository. "
                        "Draft releases are only visible to users with push access."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "per_page": {"type": "integer", "description": "The number of results per page (max 100, default 30)."},
                            "page": {"type": "integer", "description": "The page number of the results to fetch (default 1)."},
                        },
                        "required": [],
                    },
                },
            },
        },
    },
    "github_project_management": {
        "list_repository_issues": {
            "id": "list_repository_issues",
            "title": "List Repository Issues",
            "description": (
                "Retrieve issues for a repository. Note: GitHub's API returns pull requests as issues; "
                "filter by absence of pull_request key to get issues only."
            ),
            "schema": {
                "type": "function",
                "function": {
                    "name": "list_repository_issues",
                    "description": (
                        "Retrieve issues for a repository. Note: GitHub's API returns pull requests as issues; "
                        "filter by absence of pull_request key to get issues only."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {"type": "string", "enum": ["open", "closed", "all"], "description": "Filter issues by state. Default: open."},
                            "labels": {"type": "string", "description": "A list of comma-separated label names."},
                            "assignee": {"type": "string", "description": "Filter by assignee login. Use 'none' for unassigned, '*' for any assignee."},
                            "sort": {"type": "string", "enum": ["created", "updated", "comments"], "description": "What to sort results by."},
                            "direction": {"type": "string", "enum": ["asc", "desc"], "description": "The direction to sort the results by."},
                            "since": {"type": "string", "description": "Only show results updated after this time (ISO 8601)."},
                            "per_page": {"type": "integer", "description": "The number of results per page (max 100)."},
                            "page": {"type": "integer", "description": "The page number of the results to fetch."},
                        },
                        "required": [],
                    },
                },
            },
        },
        "create_issue": {
            "id": "create_issue",
            "title": "Create an Issue",
            "description": "Create a new issue in a repository with a title, optional body, assignees, labels, and milestone.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "create_issue",
                    "description": "Create a new issue in a repository with a title, optional body, assignees, labels, and milestone.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "The title of the issue."},
                            "body": {"type": "string", "description": "The contents of the issue."},
                            "assignees": {"type": "array", "items": {"type": "string"}, "description": "Logins for users to assign to this issue."},
                            "milestone": {"type": "integer", "description": "The number of the milestone to associate this issue with."},
                            "labels": {"type": "array", "items": {"type": "string"}, "description": "Labels to associate with this issue."},
                        },
                        "required": ["title"],
                    },
                },
            },
        },
        "get_issue": {
            "id": "get_issue",
            "title": "Get an Issue",
            "description": "Retrieve a single issue by its number, including its state, labels, assignees, and body.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "get_issue",
                    "description": "Retrieve a single issue by its number, including its state, labels, assignees, and body.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_number": {"type": "integer", "description": "The number that identifies the issue."},
                        },
                        "required": ["issue_number"],
                    },
                },
            },
        },
        "update_issue": {
            "id": "update_issue",
            "title": "Update an Issue",
            "description": "Update an existing issue's title, body, state (open/closed), assignees, labels, or milestone.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "update_issue",
                    "description": "Update an existing issue's title, body, state (open/closed), assignees, labels, or milestone.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "The title of the issue."},
                            "body": {"type": "string", "description": "The contents of the issue."},
                            "state": {"type": "string", "enum": ["open", "closed"], "description": "The open or closed state of the issue."},
                            "assignees": {"type": "array", "items": {"type": "string"}, "description": "Logins for users to assign to this issue."},
                            "milestone": {"type": "integer", "description": "The milestone number, or null to remove."},
                            "labels": {"type": "array", "items": {"type": "string"}, "description": "Labels to associate with this issue."},
                        },
                        "required": [],
                    },
                },
            },
        },
        "lock_issue": {
            "id": "lock_issue",
            "title": "Lock an Issue",
            "description": "Lock an issue to prevent further comments. Optionally specify a lock reason: off-topic, too heated, resolved, or spam.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "lock_issue",
                    "description": "Lock an issue to prevent further comments. Optionally specify a lock reason: off-topic, too heated, resolved, or spam.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lock_reason": {"type": "string", "enum": ["off-topic", "too heated", "resolved", "spam"], "description": "The reason for locking the issue."},
                        },
                        "required": [],
                    },
                },
            },
        },
        "unlock_issue": {
            "id": "unlock_issue",
            "title": "Unlock an Issue",
            "description": "Remove the lock on an issue to allow new comments.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "unlock_issue",
                    "description": "Remove the lock on an issue to allow new comments.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        },
    },
}

TOOL_HANDLERS = {
    **PMS_GITHUB_HANDLERS,
}

INTEGRATION_HANDLERS = {
    "github_version_control": GITHUB_HANDLERS,
    "github_project_management": GITHUB_HANDLERS,
}
