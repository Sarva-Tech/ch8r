from rest_framework import serializers
from core.models import NotificationProfile

class NotificationProfileSerializer(serializers.ModelSerializer):
    config = serializers.DictField()

    class Meta:
        model = NotificationProfile
        fields = ['id', 'type', 'config', 'created_at', 'name']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        config = validated_data.pop('config', {})
        instance = NotificationProfile(**validated_data)
        instance.config = config
        instance.save()
        return instance

    def update(self, instance, validated_data):
        config = validated_data.pop('config', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if config is not None:
            instance.config = config
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['config'] = instance.config
        return data
