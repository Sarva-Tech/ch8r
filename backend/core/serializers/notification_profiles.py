import json
from rest_framework import serializers
from core.models import NotificationProfile
from core.services import decrypt_with_private_key
from core.services.encryption import encrypt_dict, decrypt_dict  # Ensure this exists


class NotificationProfileSerializer(serializers.ModelSerializer):
    config = serializers.JSONField()

    class Meta:
        model = NotificationProfile
        fields = ['id', 'uuid', 'type', 'config', 'created_at', 'name']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        config = validated_data.pop('config', {})
        instance = NotificationProfile(**validated_data)
        instance._config = encrypt_dict(config)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        config = getattr(instance, 'config', {})
        filtered_config = {}
        if isinstance(config, dict) and 'email' in config:
            filtered_config['email'] = config['email']

        representation['config'] = filtered_config
        return representation


class BulkNotificationProfileSerializer(serializers.ModelSerializer):
    config = serializers.JSONField(write_only=True)

    class Meta:
        model = NotificationProfile
        fields = ['name', 'type', 'config']

def create(self, validated_data):
    encrypted_config = validated_data.get('config')

    if isinstance(encrypted_config, str):
        try:
            encrypted_config = json.loads(encrypted_config)
        except Exception:
            raise serializers.ValidationError("Config field must be a JSON object")

    if not isinstance(encrypted_config, dict):
        raise serializers.ValidationError("Config field must be a dictionary")

    decrypted_config = {}

    for key, value in encrypted_config.items():
        if key == 'cong.email':
            decrypted_config[key] = value
        elif isinstance(value, str):
            try:
                decrypted_value = decrypt_with_private_key(value)
                decrypted_config[key] = decrypted_value
            except Exception as e:
                raise serializers.ValidationError(f"Failed to decrypt '{key}': {str(e)}")
        else:
            decrypted_config[key] = value

    instance = NotificationProfile(
        name=validated_data['name'],
        type=validated_data['type'],
        config=decrypted_config
    )
    instance.save()
    return instance
