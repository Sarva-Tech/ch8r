from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value

    def validate_new_password(self, value):
        errors = []

        if len(value) < 8:
            errors.append("Password must be at least 8 characters long")

        if not re.search(r'[a-z]', value) or not re.search(r'[A-Z]', value):
            errors.append("Password must contain both uppercase and lowercase letters")

        if not re.search(r'[0-9]', value):
            errors.append("Password must contain at least one number")

        if not re.search(r'[^a-zA-Z0-9]', value):
            errors.append("Password must contain at least one special character")

        if errors:
            raise serializers.ValidationError(errors)

        try:
            validate_password(value)
        except ValidationError as django_error:
            if isinstance(django_error.messages, list):
                errors.extend(django_error.messages)
            else:
                errors.append(str(django_error))
            raise serializers.ValidationError(errors)

        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")

        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError("New password must be different from current password")

        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
