from django.contrib.auth.models import User
from core.models import AccountStatus
from rest_framework import serializers
import requests
import os

class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )

        AccountStatus.objects.create(
            account=user,
            status='PENDING'
        )

        self.send_discord_notification("A new user has registered: " + user.email)
        return user

    def send_discord_notification(self, message):
        webhook_url = os.getenv('DISCORD_SIGNUP_WEBHOOK_URL')
        payload = {
            "content": message
        }
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
