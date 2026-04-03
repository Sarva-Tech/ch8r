from core.integrations.github_tools import GITHUB_VC_HANDLERS, GITHUB_PM_HANDLERS

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
                            "author": {"type": "string", "description": "Filter by commit author using username or email address."},
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
                "Draft releases may have visibility restrictions based on provider."
            ),
            "schema": {
                "type": "function",
                "function": {
                    "name": "list_releases",
                    "description": (
                        "Retrieve published releases for a repository. "
                        "Draft releases may have visibility restrictions based on provider."
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
        "list_tickets": {
            "id": "list_tickets",
            "title": "List Tickets",
            "description": (
                "Retrieve tickets, issues, or feedback items from a project management system. "
                "Filter by status, labels, assignee, or date range. Can be used when users ask to "
                'see tickets, list issues, view feedback, show problems, or check bug reports.'
            ),
            "schema": {
                "type": "function",
                "function": {
                    "name": "list_tickets",
                    "description": (
                        "Retrieve tickets, issues, or feedback items from a project management system. "
                        "Filter by status, labels, assignee, or date range. Can be used when users ask to "
                        'see tickets, list issues, view feedback, show problems, or check bug reports.'
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
        "create_ticket": {
            "id": "create_ticket",
            "title": "Create Ticket",
            "description": (
                "Create a new ticket, issue, or feedback entry with a title and optional details. "
                "Can be used when users ask to create a ticket, submit feedback, file an issue, "
                'report a bug, submit a problem, or log a concern.'
            ),
            "schema": {
                "type": "function",
                "function": {
                    "name": "create_ticket",
                    "description": (
                        "Create a new ticket, issue, or feedback entry with a title and optional details. "
                        "Can be used when users ask to create a ticket, submit feedback, file an issue, "
                        'report a bug, submit a problem, or log a concern.'
                    ),
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
        "get_ticket": {
            "id": "get_ticket",
            "title": "Get Ticket",
            "description": "Retrieve details of a specific ticket or issue by its identifier.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "get_ticket",
                    "description": "Retrieve details of a specific ticket or issue by its identifier.",
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
        "update_ticket": {
            "id": "update_ticket",
            "title": "Update Ticket",
            "description": "Update an existing ticket's title, description, status, assignees, or labels.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "update_ticket",
                    "description": "Update an existing ticket's title, description, status, assignees, or labels.",
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
        "lock_ticket": {
            "id": "lock_ticket",
            "title": "Lock Ticket",
            "description": "Prevent further comments on a ticket by locking it. Optionally specify a reason.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "lock_ticket",
                    "description": "Prevent further comments on a ticket by locking it. Optionally specify a reason.",
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
        "unlock_ticket": {
            "id": "unlock_ticket",
            "title": "Unlock Ticket",
            "description": "Remove the lock on a ticket to allow new comments.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "unlock_ticket",
                    "description": "Remove the lock on a ticket to allow new comments.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        },
    },
}

INTEGRATION_HANDLERS = {
    "github_version_control": GITHUB_VC_HANDLERS,
    "github_project_management": GITHUB_PM_HANDLERS,
}
