import pytest
from rest_framework import serializers
from django.contrib.auth.models import User

from core.serializers.password import (
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)
from core.tests.factories import UserFactory


@pytest.mark.unit
class TestForgotPasswordSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = ForgotPasswordSerializer()
        expected_fields = ['email']
        for field in expected_fields:
            assert field in serializer.fields

    def test_email_is_required(self):
        serializer = ForgotPasswordSerializer()
        assert serializer.fields['email'].required

    def test_validate_email_valid(self):
        user = UserFactory(email='test@example.com')

        serializer = ForgotPasswordSerializer()
        result = serializer.validate_email('test@example.com')

        assert result == 'test@example.com'

    def test_validate_email_invalid(self):
        serializer = ForgotPasswordSerializer()
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_email('nonexistent@example.com')

        assert "does not exist" in str(exc_info.value)


@pytest.mark.unit
class TestResetPasswordSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = ResetPasswordSerializer()
        expected_fields = ['password', 'confirm_password']
        for field in expected_fields:
            assert field in serializer.fields

    def test_password_is_write_only(self):
        serializer = ResetPasswordSerializer()
        assert serializer.fields['password'].write_only

    def test_confirm_password_is_write_only(self):
        serializer = ResetPasswordSerializer()
        assert serializer.fields['confirm_password'].write_only

    def test_password_min_length(self):
        serializer = ResetPasswordSerializer()
        assert serializer.fields['password'].min_length == 8

    def test_validate_passwords_match(self):
        data = {
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }

        serializer = ResetPasswordSerializer(data=data)
        assert serializer.is_valid()

    def test_validate_passwords_do_not_match(self):
        data = {
            'password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }

        serializer = ResetPasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'confirm_password' in serializer.errors
        assert "must match" in str(serializer.errors['confirm_password'])
