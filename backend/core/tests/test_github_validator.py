import pytest
from unittest.mock import Mock, patch

from core.integrations.github_validator import validate_github_token


@pytest.mark.unit
class TestValidateGithubToken:
    def test_validate_github_token_missing_token(self):
        credentials = {}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert message == 'Token is required'
        assert metadata == {}

    def test_validate_github_token_empty_token(self):
        credentials = {'token': ''}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert message == 'Token is required'
        assert metadata == {}

    def test_validate_github_token_none_token(self):
        credentials = {'token': None}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert message == 'Token is required'
        assert metadata == {}

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'login': 'testuser',
            'name': 'Test User',
            'avatar_url': 'https://github.com/testuser.png',
            'html_url': 'https://github.com/testuser'
        }
        mock_get.return_value = mock_response

        credentials = {'token': 'ghp_test_token_123'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is True
        assert message == ''
        assert metadata['login'] == 'testuser'
        assert metadata['name'] == 'Test User'
        assert metadata['avatar_url'] == 'https://github.com/testuser.png'
        assert metadata['html_url'] == 'https://github.com/testuser'

        mock_get.assert_called_once_with(
            'https://api.github.com/user',
            headers={
                'Authorization': 'Bearer ghp_test_token_123',
                'Accept': 'application/vnd.github+json',
            },
            timeout=10,
        )

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_partial_metadata(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'login': 'testuser',
            'avatar_url': 'https://github.com/testuser.png'
        }
        mock_get.return_value = mock_response

        credentials = {'token': 'ghp_test_token_123'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is True
        assert message == ''
        assert metadata['login'] == 'testuser'
        assert metadata['name'] is None
        assert metadata['avatar_url'] == 'https://github.com/testuser.png'
        assert metadata['html_url'] is None

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_unauthorized(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        credentials = {'token': 'invalid_token'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert message == 'GitHub returned 401'
        assert metadata == {}

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_forbidden(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        credentials = {'token': 'forbidden_token'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert message == 'GitHub returned 403'
        assert metadata == {}

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_not_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        credentials = {'token': 'not_found_token'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert message == 'GitHub returned 404'
        assert metadata == {}

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_server_error(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        credentials = {'token': 'server_error_token'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert message == 'GitHub returned 500'
        assert metadata == {}

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_timeout(self, mock_get):
        import requests
        mock_get.side_effect = requests.Timeout("Connection timed out")

        credentials = {'token': 'timeout_token'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert 'timed out' in message.lower() or 'timeout' in message.lower()
        assert metadata == {}

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_connection_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.ConnectionError("Failed to establish connection")

        credentials = {'token': 'connection_error_token'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert 'connection' in message.lower() or 'failed' in message.lower()
        assert metadata == {}

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_request_exception(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Generic error")

        credentials = {'token': 'error_token'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert message == 'Generic error'
        assert metadata == {}

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_http_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.HTTPError("HTTP Error occurred")

        credentials = {'token': 'http_error_token'}
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is False
        assert 'http error' in message.lower()
        assert metadata == {}

    @patch("core.integrations.github_validator.requests.get")
    def test_validate_github_token_with_extra_credentials_fields(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'login': 'testuser',
            'name': 'Test User',
            'avatar_url': 'https://github.com/testuser.png',
            'html_url': 'https://github.com/testuser'
        }
        mock_get.return_value = mock_response

        credentials = {
            'token': 'ghp_test_token_123',
            'extra_field': 'ignored',
            'another_field': 'also_ignored'
        }
        is_valid, message, metadata = validate_github_token(credentials)

        assert is_valid is True
        assert message == ''
        assert metadata['login'] == 'testuser'
