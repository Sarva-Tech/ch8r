import pytest
from unittest.mock import Mock, patch
import base64

from core.services.private_key_encryption import decrypt_with_private_key


@pytest.mark.unit
class TestDecryptWithPrivateKey:
    @patch('core.services.private_key_encryption.PRIVATE_KEY_PEM')
    @patch('core.services.private_key_encryption.serialization.load_pem_private_key')
    def test_decrypt_with_private_key_success(self, mock_load_key, mock_private_key):
        mock_private_key.return_value = '-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----'

        mock_key_instance = Mock()
        mock_key_instance.decrypt.return_value = b'decrypted_data'
        mock_load_key.return_value = mock_key_instance

        encrypted_data = base64.b64encode(b'encrypted_bytes').decode()
        result = decrypt_with_private_key(encrypted_data)

        assert result == 'decrypted_data'
        mock_key_instance.decrypt.assert_called_once()

    @patch('core.services.private_key_encryption.PRIVATE_KEY_PEM', None)
    def test_decrypt_with_private_key_missing_key(self):
        encrypted_data = base64.b64encode(b'encrypted_bytes').decode()

        with pytest.raises(ValueError, match="Missing PRIVATE_KEY in environment"):
            decrypt_with_private_key(encrypted_data)

    @patch('core.services.private_key_encryption.PRIVATE_KEY_PEM')
    @patch('core.services.private_key_encryption.serialization.load_pem_private_key')
    def test_decrypt_with_private_key_invalid_base64(self, mock_load_key, mock_private_key):
        mock_private_key.return_value = '-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----'

        mock_key_instance = Mock()
        mock_load_key.return_value = mock_key_instance

        with pytest.raises(Exception):
            decrypt_with_private_key('invalid_base64!')

    @patch('core.services.private_key_encryption.PRIVATE_KEY_PEM')
    @patch('core.services.private_key_encryption.serialization.load_pem_private_key')
    def test_decrypt_with_private_key_empty_string(self, mock_load_key, mock_private_key):
        mock_private_key.return_value = '-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----'

        mock_key_instance = Mock()
        mock_key_instance.decrypt.return_value = b''
        mock_load_key.return_value = mock_key_instance

        encrypted_data = base64.b64encode(b'encrypted_bytes').decode()
        result = decrypt_with_private_key(encrypted_data)

        assert result == ''

    @patch('core.services.private_key_encryption.PRIVATE_KEY_PEM')
    @patch('core.services.private_key_encryption.serialization.load_pem_private_key')
    def test_decrypt_with_private_key_unicode_content(self, mock_load_key, mock_private_key):
        mock_private_key.return_value = '-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----'

        mock_key_instance = Mock()
        mock_key_instance.decrypt.return_value = 'Hello there'.encode('utf-8')
        mock_load_key.return_value = mock_key_instance

        encrypted_data = base64.b64encode(b'encrypted_bytes').decode()
        result = decrypt_with_private_key(encrypted_data)

        assert result == 'Hello there'

    @patch('core.services.private_key_encryption.PRIVATE_KEY_PEM')
    @patch('core.services.private_key_encryption.serialization.load_pem_private_key')
    def test_decrypt_with_private_key_long_content(self, mock_load_key, mock_private_key):
        mock_private_key.return_value = '-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----'

        long_content = 'a' * 1000
        mock_key_instance = Mock()
        mock_key_instance.decrypt.return_value = long_content.encode('utf-8')
        mock_load_key.return_value = mock_key_instance

        encrypted_data = base64.b64encode(b'encrypted_bytes').decode()
        result = decrypt_with_private_key(encrypted_data)

        assert result == long_content
        assert len(result) == 1000
