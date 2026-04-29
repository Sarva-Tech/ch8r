import pytest
from unittest.mock import Mock, patch
from core.integrations.github_tools import add_comment


@pytest.mark.unit
class TestAddComment:
    @patch("core.integrations.github_tools._gh_request")
    @patch("core.integrations.github_tools._creds")
    def test_add_comment_success(self, mock_creds, mock_request):
        # Setup mocks
        mock_creds.return_value = ("test_token", "owner/repo")
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 12345,
            "body": "This is a test comment",
            "created_at": "2023-01-01T12:00:00Z"
        }
        mock_request.return_value = mock_response
        
        # Setup app integration mock
        mock_app_integration = Mock()
        
        # Call the function
        result = add_comment(mock_app_integration, issue_number=42, body="This is a test comment")
        
        # Verify the request was made correctly
        mock_request.assert_called_once_with(
            "post",
            "https://api.github.com/repos/owner/repo/issues/42/comments",
            headers={
                "Authorization": "Bearer test_token",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            },
            json={"body": "This is a test comment"}
        )
        
        # Verify the result
        expected = {
            "id": 12345,
            "body": "This is a test comment",
            "issue_number": 42,
            "created_at": "2023-01-01T12:00:00Z"
        }
        assert result == expected

    def test_add_comment_missing_issue_number(self):
        mock_app_integration = Mock()
        
        with pytest.raises(ValueError) as exc_info:
            add_comment(mock_app_integration, body="Test comment")
        
        assert "Missing required parameter: issue_number" in str(exc_info.value)

    def test_add_comment_missing_body(self):
        mock_app_integration = Mock()
        
        with pytest.raises(ValueError) as exc_info:
            add_comment(mock_app_integration, issue_number=42)
        
        assert "Missing required parameter: body" in str(exc_info.value)
