from django.contrib.auth.models import User
from rest_framework import serializers
from core.models import AccountStatus
from core.services.encryption import generate_verification_token
from core.tasks.email import send_verification_email_task, send_discord_notification_task


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            is_active=False
        )

        AccountStatus.objects.create(
            account=user,
            status='PENDING'
        )

        verification_token = generate_verification_token(user.id, user.email)

        send_verification_email_task.delay(user.id, user.email, user.username, verification_token)
        send_discord_notification_task.delay(f"A new user has registered: {user.email}")

        return user

class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
