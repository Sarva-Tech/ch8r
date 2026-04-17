import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json
import base64
from cryptography.fernet import Fernet

from core.services.encryption import (
    encrypt,
    decrypt,
    _get_fernet,
    generate_verification_token,
    verify_verification_token
)

VALID_FERNET_KEY = Fernet.generate_key().decode()

@pytest.mark.unit
class TestEncrypt:
    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_encrypt_string_success(self):
        result = encrypt('test string')

        assert isinstance(result, str)
        assert result != 'test string'

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_encrypt_dict_success(self):
        data = {'key1': 'value1', 'key2': 'value2'}
        result = encrypt(data)

        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert 'key1' in result_dict
        assert 'key2' in result_dict

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_encrypt_empty_dict(self):
        result = encrypt({})

        assert result == json.dumps({})

    @patch('core.services.encryption.key', None)
    def test_encrypt_missing_key(self):
        with pytest.raises(ValueError, match="Missing SECRET_ENCRYPTION_KEY in settings"):
            encrypt('test string')

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_encrypt_invalid_type(self):
        with pytest.raises(TypeError, match="Data must be a dict or str"):
            encrypt(123)

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_encrypt_dict_with_numeric_values(self):
        data = {'key1': 123, 'key2': 456.78}
        result = encrypt(data)

        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert 'key1' in result_dict
        assert 'key2' in result_dict

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_encrypt_empty_string(self):
        result = encrypt('')

        assert isinstance(result, str)
        assert result != ''


@pytest.mark.unit
class TestDecrypt:
    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_decrypt_string_success(self):
        encrypted = encrypt('test string')
        result = decrypt(encrypted)

        assert result == 'test string'

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_decrypt_dict_success(self):
        data = {'key1': 'value1', 'key2': 'value2'}
        encrypted = encrypt(data)
        result = decrypt(encrypted)

        assert result == data

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_decrypt_empty_dict(self):
        encrypted = encrypt({})
        result = decrypt(encrypted)

        assert result == {}

    @patch('core.services.encryption.key', None)
    def test_decrypt_missing_key(self):
        with pytest.raises(ValueError, match="Missing SECRET_ENCRYPTION_KEY in settings"):
            decrypt('encrypted_string')

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_decrypt_invalid_string(self):
        result = decrypt('invalid_encrypted_string')

        assert result == {}

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_decrypt_round_trip_dict(self):
        original = {'username': 'testuser', 'email': 'test@example.com', 'age': '30'}
        encrypted = encrypt(original)
        decrypted = decrypt(encrypted)

        assert decrypted == original

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_decrypt_round_trip_string(self):
        original = 'This is a test string with special characters: !@#$%^&*()'
        encrypted = encrypt(original)
        decrypted = decrypt(encrypted)

        assert decrypted == original


@pytest.mark.unit
class TestGetFernet:
    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_get_fernet_success(self):
        fernet = _get_fernet()

        assert fernet is not None

    @patch('core.services.encryption.key', None)
    def test_get_fernet_missing_key(self):
        with pytest.raises(ValueError, match="Missing SECRET_ENCRYPTION_KEY in settings"):
            _get_fernet()


@pytest.mark.unit
class TestGenerateVerificationToken:
    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_generate_verification_token_success(self):
        token = generate_verification_token(123, 'test@example.com')

        assert isinstance(token, str)
        assert len(token) > 0

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_generate_verification_token_includes_payload(self):
        token = generate_verification_token(456, 'user@test.com')

        decoded = base64.urlsafe_b64decode(token.encode())
        assert decoded is not None

    @patch('core.services.encryption.key', None)
    def test_generate_verification_token_missing_key(self):
        with pytest.raises(ValueError, match="Missing SECRET_ENCRYPTION_KEY in settings"):
            generate_verification_token(123, 'test@example.com')

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_generate_verification_token_different_inputs(self):
        token1 = generate_verification_token(1, 'user1@test.com')
        token2 = generate_verification_token(2, 'user2@test.com')

        assert token1 != token2


@pytest.mark.unit
class TestVerifyVerificationToken:
    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_verify_verification_token_success(self):
        token = generate_verification_token(123, 'test@example.com')
        payload, error = verify_verification_token(token)

        assert error is None
        assert payload is not None
        assert payload['user_id'] == 123
        assert payload['email'] == 'test@example.com'
        assert 'exp' in payload

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_verify_verification_token_invalid_token(self):
        payload, error = verify_verification_token('invalid_token')

        assert payload is None
        assert error is not None
        assert 'Invalid token' in error

    @patch('core.services.encryption.key', VALID_FERNET_KEY)
    def test_verify_verification_token_expired(self):
        with patch('core.services.encryption.datetime') as mock_datetime:
            past_time = datetime.now() - timedelta(hours=25)
            mock_datetime.now.return_value = past_time
            mock_datetime.fromisoformat = datetime.fromisoformat

            token = generate_verification_token(123, 'test@example.com')

        payload, error = verify_verification_token(token)

        assert payload is None
        assert error == 'Token has expired'

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_verify_verification_token_malformed(self):
        payload, error = verify_verification_token('not_a_valid_token')

        assert payload is None
        assert error is not None

    @patch('core.services.encryption.key', None)
    def test_verify_verification_token_missing_key(self):
        token = 'some_token'
        payload, error = verify_verification_token(token)

        assert payload is None
        assert error is not None

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_verify_verification_token_round_trip(self):
        user_id = 999
        email = 'roundtrip@test.com'

        token = generate_verification_token(user_id, email)
        payload, error = verify_verification_token(token)

        assert error is None
        assert payload['user_id'] == user_id
        assert payload['email'] == email

    @patch('core.services.encryption.SECRET_ENCRYPTION_KEY', VALID_FERNET_KEY)
    def test_verify_verification_token_within_expiry(self):
        token = generate_verification_token(123, 'test@example.com')
        payload, error = verify_verification_token(token)

        assert error is None
        assert payload is not None

        exp_time = datetime.fromisoformat(payload['exp'])
        assert datetime.now() < exp_time
