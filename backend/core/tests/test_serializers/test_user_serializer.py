import pytest
from rest_framework import serializers
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from core.serializers.user import (
    UserRegisterSerializer,
    UserViewSerializer,
)
from core.models import AccountStatus


@pytest.mark.unit
class TestUserRegisterSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = UserRegisterSerializer()
        expected_fields = ['id', 'username', 'email', 'password']
        for field in expected_fields:
            assert field in serializer.fields

    def test_password_is_write_only(self):
        serializer = UserRegisterSerializer()
        assert serializer.fields['password'].write_only

    def test_create_creates_user(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }

        with patch('core.serializers.user.generate_verification_token') as mock_token, \
             patch('core.serializers.user.send_verification_email_task') as mock_email, \
             patch('core.serializers.user.send_discord_notification_task') as mock_discord:
            mock_token.return_value = 'test_token'

            serializer = UserRegisterSerializer(data=data)
            assert serializer.is_valid()
            user = serializer.save()

            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert not user.is_active

    def test_create_creates_account_status(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }

        with patch('core.serializers.user.generate_verification_token') as mock_token, \
             patch('core.serializers.user.send_verification_email_task') as mock_email, \
             patch('core.serializers.user.send_discord_notification_task') as mock_discord:
            mock_token.return_value = 'test_token'

            serializer = UserRegisterSerializer(data=data)
            assert serializer.is_valid()
            user = serializer.save()

            account_status = AccountStatus.objects.get(account=user)
            assert account_status.status == 'PENDING'

    def test_create_generates_verification_token(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }

        with patch('core.serializers.user.generate_verification_token') as mock_token, \
             patch('core.serializers.user.send_verification_email_task') as mock_email, \
             patch('core.serializers.user.send_discord_notification_task') as mock_discord:
            mock_token.return_value = 'test_token'

            serializer = UserRegisterSerializer(data=data)
            assert serializer.is_valid()
            serializer.save()

            mock_token.assert_called_once()

    def test_create_sends_verification_email(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }

        with patch('core.serializers.user.generate_verification_token') as mock_token, \
             patch('core.serializers.user.send_verification_email_task') as mock_email, \
             patch('core.serializers.user.send_discord_notification_task') as mock_discord:
            mock_token.return_value = 'test_token'

            serializer = UserRegisterSerializer(data=data)
            assert serializer.is_valid()
            user = serializer.save()

            mock_email.delay.assert_called_once()

    def test_create_sends_discord_notification(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }

        with patch('core.serializers.user.generate_verification_token') as mock_token, \
             patch('core.serializers.user.send_verification_email_task') as mock_email, \
             patch('core.serializers.user.send_discord_notification_task') as mock_discord:
            mock_token.return_value = 'test_token'

            serializer = UserRegisterSerializer(data=data)
            assert serializer.is_valid()
            serializer.save()

            mock_discord.delay.assert_called_once_with(f"A new user has registered: test@example.com")


@pytest.mark.unit
class TestUserViewSerializer:
    def test_serialization_includes_expected_fields(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        serializer = UserViewSerializer(user)
        data = serializer.data

        expected_fields = ['id', 'username', 'email', 'first_name', 'last_name']
        for field in expected_fields:
            assert field in data

    def test_serialization_excludes_password(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        serializer = UserViewSerializer(user)
        data = serializer.data

        assert 'password' not in data
