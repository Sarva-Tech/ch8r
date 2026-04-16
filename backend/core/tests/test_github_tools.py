import pytest
from unittest.mock import Mock, patch, MagicMock

from core.integrations.github_tools import (
    _headers,
    _creds,
    _gh_request,
    list_commits,
    list_pull_requests,
    list_releases,
    list_tickets,
    create_ticket,
    get_ticket,
    update_ticket,
    lock_ticket,
    unlock_ticket,
    GITHUB_API,
    GITHUB_API_VERSION,
    GITHUB_VC_HANDLERS,
    GITHUB_PM_HANDLERS,
)


@pytest.mark.unit
class TestHeaders:
    def test_headers_basic(self):
        result = _headers("test_token_123")
        assert result["Authorization"] == "Bearer test_token_123"
        assert result["Accept"] == "application/vnd.github+json"
        assert result["X-GitHub-Api-Version"] == GITHUB_API_VERSION

    def test_headers_empty_token(self):
        result = _headers("")
        assert result["Authorization"] == "Bearer "
        assert result["Accept"] == "application/vnd.github+json"


@pytest.mark.unit
class TestCreds:
    def test_creds_basic(self):
        app_integration = Mock()
        app_integration.integration.credentials = '{"token": "ghp_test_token"}'
        app_integration.metadata = {"repo": "owner/repo"}

        token, repo = _creds(app_integration)
        assert token == "ghp_test_token"
        assert repo == "owner/repo"

    def test_creds_no_metadata(self):
        app_integration = Mock()
        app_integration.integration.credentials = '{"token": "ghp_test_token"}'
        app_integration.metadata = None

        token, repo = _creds(app_integration)
        assert token == "ghp_test_token"
        assert repo == ""

    def test_creds_empty_metadata(self):
        app_integration = Mock()
        app_integration.integration.credentials = '{"token": "ghp_test_token"}'
        app_integration.metadata = {}

        token, repo = _creds(app_integration)
        assert token == "ghp_test_token"
        assert repo == ""

    def test_creds_no_repo_in_metadata(self):
        app_integration = Mock()
        app_integration.integration.credentials = '{"token": "ghp_test_token"}'
        app_integration.metadata = {"other_field": "value"}

        token, repo = _creds(app_integration)
        assert token == "ghp_test_token"
        assert repo == ""


@pytest.mark.unit
class TestGhRequest:
    @patch("core.integrations.github_tools.requests.request")
    def test_gh_request_get(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "100"}
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        headers = {"Authorization": "Bearer token"}
        result = _gh_request("get", f"{GITHUB_API}/test", headers=headers)

        mock_request.assert_called_once_with("get", f"{GITHUB_API}/test", headers=headers, params=None, json=None, timeout=15)
        assert result.status_code == 200

    @patch("core.integrations.github_tools.requests.request")
    def test_gh_request_with_params(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "50"}
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        headers = {"Authorization": "Bearer token"}
        params = {"state": "open", "per_page": 10}
        result = _gh_request("get", f"{GITHUB_API}/test", headers=headers, params=params)

        mock_request.assert_called_once_with("get", f"{GITHUB_API}/test", headers=headers, params=params, json=None, timeout=15)

    @patch("core.integrations.github_tools.requests.request")
    def test_gh_request_post_with_json(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"content-length": "200"}
        mock_response.json.return_value = {"id": 1}
        mock_request.return_value = mock_response

        headers = {"Authorization": "Bearer token"}
        json_data = {"title": "Test Issue"}
        result = _gh_request("post", f"{GITHUB_API}/test", headers=headers, json=json_data)

        mock_request.assert_called_once_with("post", f"{GITHUB_API}/test", headers=headers, params=None, json=json_data, timeout=15)

    @patch("core.integrations.github_tools.requests.request")
    def test_gh_request_raises_on_error(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_request.return_value = mock_response

        headers = {"Authorization": "Bearer token"}

        with pytest.raises(Exception):
            _gh_request("get", f"{GITHUB_API}/test", headers=headers)


@pytest.mark.unit
class TestListCommits:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_commits_basic(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "sha": "abc123def456",
                "commit": {
                    "message": "First commit\n\nSome details",
                    "author": {"name": "John Doe", "date": "2024-01-01T00:00:00Z"}
                }
            },
            {
                "sha": "def456ghi789",
                "commit": {
                    "message": "Second commit",
                    "author": {"name": "Jane Smith", "date": "2024-01-02T00:00:00Z"}
                }
            }
        ]
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = list_commits(app_integration)

        assert len(result) == 2
        assert result[0]["sha"] == "abc123d"
        assert result[0]["message"] == "First commit"
        assert result[0]["author"] == "John Doe"
        assert result[1]["sha"] == "def456g"
        assert result[1]["message"] == "Second commit"

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_commits_with_params(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "sha": "abc123def456",
                "commit": {
                    "message": "Feature commit",
                    "author": {"name": "John Doe", "date": "2024-01-01T00:00:00Z"}
                }
            }
        ]
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = list_commits(app_integration, sha="main", path="src/", author="john")

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "sha" in call_args[1]["params"]
        assert call_args[1]["params"]["sha"] == "main"
        assert call_args[1]["params"]["path"] == "src/"
        assert call_args[1]["params"]["author"] == "john"

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_commits_filters_none_params(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        app_integration = Mock()
        list_commits(app_integration, sha="main", path=None, author=None)

        call_args = mock_request.call_args
        assert call_args[1]["params"]["sha"] == "main"
        assert "path" not in call_args[1]["params"]
        assert "author" not in call_args[1]["params"]


@pytest.mark.unit
class TestListPullRequests:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_pull_requests_basic(self, mock_creds, mock_request):
        """Test listing pull requests with default state."""
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "number": 1,
                "title": "Add new feature",
                "state": "open",
                "user": {"login": "john"},
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = list_pull_requests(app_integration)

        assert len(result) == 1
        assert result[0]["number"] == 1
        assert result[0]["title"] == "Add new feature"
        assert result[0]["state"] == "open"
        assert result[0]["author"] == "john"

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_pull_requests_default_state(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        app_integration = Mock()
        list_pull_requests(app_integration)

        call_args = mock_request.call_args
        assert call_args[1]["params"]["state"] == "open"

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_pull_requests_with_params(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        app_integration = Mock()
        list_pull_requests(app_integration, state="closed", base="main", sort="updated")

        call_args = mock_request.call_args
        assert call_args[1]["params"]["state"] == "closed"
        assert call_args[1]["params"]["base"] == "main"
        assert call_args[1]["params"]["sort"] == "updated"


@pytest.mark.unit
class TestListReleases:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_releases_basic(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "tag_name": "v1.0.0",
                "name": "First Release",
                "draft": False,
                "prerelease": False,
                "published_at": "2024-01-01T00:00:00Z"
            },
            {
                "tag_name": "v2.0.0-beta",
                "name": "Beta Release",
                "draft": False,
                "prerelease": True,
                "published_at": "2024-02-01T00:00:00Z"
            }
        ]
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = list_releases(app_integration)

        assert len(result) == 2
        assert result[0]["tag"] == "v1.0.0"
        assert result[0]["name"] == "First Release"
        assert result[0]["draft"] is False
        assert result[0]["prerelease"] is False
        assert result[1]["tag"] == "v2.0.0-beta"
        assert result[1]["prerelease"] is True


@pytest.mark.unit
class TestListTickets:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_tickets_basic(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "number": 1,
                "title": "Bug report",
                "state": "open",
                "labels": [{"name": "bug"}, {"name": "high-priority"}],
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "number": 2,
                "title": "Feature request",
                "state": "open",
                "labels": [{"name": "enhancement"}],
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = list_tickets(app_integration)

        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[0]["title"] == "Bug report"
        assert result[0]["labels"] == ["bug", "high-priority"]
        assert result[1]["labels"] == ["enhancement"]

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_tickets_filters_pull_requests(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "number": 1,
                "title": "Regular issue",
                "state": "open",
                "labels": [],
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "number": 2,
                "title": "Pull request",
                "state": "open",
                "labels": [],
                "created_at": "2024-01-02T00:00:00Z",
                "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/2"}
            }
        ]
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = list_tickets(app_integration)

        assert len(result) == 1
        assert result[0]["number"] == 1
        assert result[0]["title"] == "Regular issue"

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_list_tickets_default_state(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        app_integration = Mock()
        list_tickets(app_integration)

        call_args = mock_request.call_args
        assert call_args[1]["params"]["state"] == "open"


@pytest.mark.unit
class TestCreateTicket:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_create_ticket_basic(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {
            "number": 1,
            "title": "New Issue",
            "state": "open"
        }
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = create_ticket(app_integration, title="New Issue")

        assert result["number"] == 1
        assert result["title"] == "New Issue"
        assert result["state"] == "open"

        call_args = mock_request.call_args
        assert call_args[0][0] == "post"
        assert call_args[0][1] == f"{GITHUB_API}/repos/owner/repo/issues"
        assert call_args[1]["json"]["title"] == "New Issue"

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_create_ticket_with_optional_fields(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {
            "number": 1,
            "title": "New Issue",
            "state": "open"
        }
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = create_ticket(
            app_integration,
            title="New Issue",
            body="Issue description",
            labels=["bug", "high-priority"],
            assignees=["john"]
        )

        call_args = mock_request.call_args
        assert call_args[1]["json"]["body"] == "Issue description"
        assert call_args[1]["json"]["labels"] == ["bug", "high-priority"]
        assert call_args[1]["json"]["assignees"] == ["john"]

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_create_ticket_ignores_none_fields(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {
            "number": 1,
            "title": "New Issue",
            "state": "open"
        }
        mock_request.return_value = mock_response

        app_integration = Mock()
        create_ticket(
            app_integration,
            title="New Issue",
            body=None,
            labels=None,
            assignees=None
        )

        call_args = mock_request.call_args
        assert "body" not in call_args[1]["json"]
        assert "labels" not in call_args[1]["json"]
        assert "assignees" not in call_args[1]["json"]


@pytest.mark.unit
class TestGetTicket:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_get_ticket_basic(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {
            "number": 1,
            "title": "Issue Title",
            "state": "open",
            "body": "Issue description",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "john"}]
        }
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = get_ticket(app_integration, issue_number=1)

        assert result["number"] == 1
        assert result["title"] == "Issue Title"
        assert result["state"] == "open"
        assert result["body"] == "Issue description"
        assert result["labels"] == ["bug"]
        assert result["assignees"] == ["john"]

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_get_ticket_empty_body(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {
            "number": 1,
            "title": "Issue Title",
            "state": "open",
            "labels": [],
            "assignees": []
        }
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = get_ticket(app_integration, issue_number=1)

        assert result["body"] == ""
        assert result["labels"] == []
        assert result["assignees"] == []


@pytest.mark.unit
class TestUpdateTicket:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_update_ticket_basic(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {
            "number": 1,
            "title": "Updated Title",
            "state": "closed"
        }
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = update_ticket(app_integration, issue_number=1, title="Updated Title", state="closed")

        assert result["number"] == 1
        assert result["title"] == "Updated Title"
        assert result["state"] == "closed"

        call_args = mock_request.call_args
        assert call_args[0][0] == "patch"
        assert call_args[0][1] == f"{GITHUB_API}/repos/owner/repo/issues/1"
        assert call_args[1]["json"]["title"] == "Updated Title"
        assert call_args[1]["json"]["state"] == "closed"
        assert "issue_number" not in call_args[1]["json"]

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_update_ticket_filters_invalid_fields(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {
            "number": 1,
            "title": "Updated Title",
            "state": "open"
        }
        mock_request.return_value = mock_response

        app_integration = Mock()
        update_ticket(
            app_integration,
            issue_number=1,
            title="Updated Title",
            body="New description",
            invalid_field="should not be included"
        )

        call_args = mock_request.call_args
        assert "title" in call_args[1]["json"]
        assert "body" in call_args[1]["json"]
        assert "invalid_field" not in call_args[1]["json"]


@pytest.mark.unit
class TestLockTicket:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_lock_ticket_basic(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = lock_ticket(app_integration, issue_number=1)

        assert result["locked"] is True
        assert result["issue_number"] == 1

        call_args = mock_request.call_args
        assert call_args[0][0] == "put"
        assert call_args[0][1] == f"{GITHUB_API}/repos/owner/repo/issues/1/lock"
        assert call_args[1]["json"] == {}

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_lock_ticket_with_reason(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = lock_ticket(app_integration, issue_number=1, lock_reason="spam")

        assert result["locked"] is True

        call_args = mock_request.call_args
        assert call_args[1]["json"]["lock_reason"] == "spam"

    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_lock_ticket_without_reason(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        app_integration = Mock()
        lock_ticket(app_integration, issue_number=1, lock_reason=None)

        call_args = mock_request.call_args
        assert "lock_reason" not in call_args[1]["json"]


@pytest.mark.unit
class TestUnlockTicket:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_unlock_ticket(self, mock_creds, mock_request):
        mock_creds.return_value = ("ghp_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        app_integration = Mock()
        result = unlock_ticket(app_integration, issue_number=1)

        assert result["locked"] is False
        assert result["issue_number"] == 1

        call_args = mock_request.call_args
        assert call_args[0][0] == "delete"
        assert call_args[0][1] == f"{GITHUB_API}/repos/owner/repo/issues/1/lock"


@pytest.mark.unit
class TestHandlerDictionaries:
    def test_github_vc_handlers(self):
        assert "list_commits" in GITHUB_VC_HANDLERS
        assert "list_pull_requests" in GITHUB_VC_HANDLERS
        assert "list_releases" in GITHUB_VC_HANDLERS
        assert GITHUB_VC_HANDLERS["list_commits"] == list_commits
        assert GITHUB_VC_HANDLERS["list_pull_requests"] == list_pull_requests
        assert GITHUB_VC_HANDLERS["list_releases"] == list_releases

    def test_github_pm_handlers(self):
        assert "list_tickets" in GITHUB_PM_HANDLERS
        assert "create_ticket" in GITHUB_PM_HANDLERS
        assert "get_ticket" in GITHUB_PM_HANDLERS
        assert "update_ticket" in GITHUB_PM_HANDLERS
        assert "lock_ticket" in GITHUB_PM_HANDLERS
        assert "unlock_ticket" in GITHUB_PM_HANDLERS
        assert GITHUB_PM_HANDLERS["list_tickets"] == list_tickets
        assert GITHUB_PM_HANDLERS["create_ticket"] == create_ticket
        assert GITHUB_PM_HANDLERS["get_ticket"] == get_ticket
        assert GITHUB_PM_HANDLERS["update_ticket"] == update_ticket
        assert GITHUB_PM_HANDLERS["lock_ticket"] == lock_ticket
        assert GITHUB_PM_HANDLERS["unlock_ticket"] == unlock_ticket
