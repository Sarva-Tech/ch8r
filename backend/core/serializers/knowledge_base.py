from rest_framework import serializers

from core.models import KnowledgeBase

class KnowledgeBaseItemSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['file', 'text', 'url'])
    value = serializers.CharField(required=False, allow_null=True)
    file = serializers.FileField(required=False, allow_null=True)

    def validate(self, data):
        item_type = data.get("type")

        if item_type == "file":
            if not data.get("value") and not data.get("file"):
                raise serializers.ValidationError({"file": "File is required for type 'file'."})
        elif item_type == "text":
            if not data.get("value"):
                raise serializers.ValidationError({"value": "Text value is required for type 'text'."})
        elif item_type == "url":
            if not data.get("value"):
                raise serializers.ValidationError({"value": "URL value is required for type 'url'."})

        return data


class KnowledgeBaseCreateSerializer(serializers.Serializer):
    items = KnowledgeBaseItemSerializer(many=True)

    def create(self, validated_data):
        return validated_data

class KnowledgeBaseViewSerializer(serializers.ModelSerializer):
    application_id = serializers.IntegerField(source='application.id', read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = ['id', 'uuid', 'application_id', 'path', 'metadata', 'source_type', 'status']
