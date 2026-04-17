import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.serializers.change_password import ChangePasswordSerializer
from core.tests.factories import UserFactory


@pytest.mark.unit
class TestChangePasswordSerializer:
    def test_serializer_includes_expected_fields(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        expected_fields = ['current_password', 'new_password', 'confirm_password']
        for field in expected_fields:
            assert field in serializer.fields

    def test_fields_are_write_only(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        assert serializer.fields['current_password'].write_only
        assert serializer.fields['new_password'].write_only
        assert serializer.fields['confirm_password'].write_only

    def test_validate_current_password_correct(self):
        user = UserFactory()
        user.set_password('oldpassword123')
        user.save()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        result = serializer.validate_current_password('oldpassword123')

        assert result == 'oldpassword123'

    def test_validate_current_password_incorrect(self):
        user = UserFactory()
        user.set_password('oldpassword123')
        user.save()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_current_password('wrongpassword')

        assert "incorrect" in str(exc_info.value).lower()

    def test_validate_new_password_too_short(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_new_password('Short1!')

        assert "8 characters" in str(exc_info.value)

    def test_validate_new_password_missing_uppercase(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_new_password('lowercase123!')

        assert "uppercase" in str(exc_info.value).lower()

    def test_validate_new_password_missing_lowercase(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_new_password('UPPERCASE123!')

        assert "lowercase" in str(exc_info.value).lower()

    def test_validate_new_password_missing_number(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_new_password('NoNumber!')

        assert "number" in str(exc_info.value).lower()

    def test_validate_new_password_missing_special_character(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_new_password('NoSpecial123')

        assert "special" in str(exc_info.value).lower()

    def test_validate_new_password_valid(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        result = serializer.validate_new_password('ValidPass123!')

        assert result == 'ValidPass123!'

    def test_validate_passwords_match(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        attrs = {
            'current_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!'
        }

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        result = serializer.validate(attrs)

        assert result == attrs

    def test_validate_passwords_dont_match(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        attrs = {
            'current_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'confirm_password': 'DifferentPass123!'
        }

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate(attrs)

        assert "don't match" in str(exc_info.value)

    def test_validate_new_password_same_as_current(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        attrs = {
            'current_password': 'SamePass123!',
            'new_password': 'SamePass123!',
            'confirm_password': 'SamePass123!'
        }

        serializer = ChangePasswordSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate(attrs)

        assert "different" in str(exc_info.value).lower()

    def test_save_sets_new_password(self):
        user = UserFactory()
        user.set_password('OldPass123!')
        user.save()
        mock_request = Mock()
        mock_request.user = user

        data = {
            'current_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!'
        }

        serializer = ChangePasswordSerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        updated_user = serializer.save()

        assert updated_user.check_password('NewPass123!')
        assert not updated_user.check_password('OldPass123!')

    def test_full_validation_flow(self):
        user = UserFactory()
        user.set_password('OldPass123!')
        user.save()
        mock_request = Mock()
        mock_request.user = user

        data = {
            'current_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'confirm_password': 'NewPass456!'
        }

        serializer = ChangePasswordSerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        updated_user = serializer.save()

        assert updated_user.check_password('NewPass456!')
