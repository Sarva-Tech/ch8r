from rest_framework import serializers

from core.models import KnowledgeBase

class KnowledgeBaseCreateSerializer(serializers.Serializer):
    source_type = serializers.ChoiceField(choices=['youtube', 'url', 'text', 'file'])
    url = serializers.URLField(required=False)
    text = serializers.CharField(required=False)
    file = serializers.FileField(required=False)

    def validate(self, data):
        source_type = data.get('source_type')
        if source_type == 'youtube' and not data.get('url'):
            raise serializers.ValidationError("YouTube URL is required.")
        if source_type == 'url' and not data.get('url'):
            raise serializers.ValidationError("URL is required.")
        if source_type == 'text' and not data.get('text'):
            raise serializers.ValidationError("Text is required.")
        if source_type == 'file' and not data.get('file'):
            raise serializers.ValidationError("File is required.")
        return data

class KnowledgeBaseViewSerializer(serializers.ModelSerializer):
    application_id = serializers.IntegerField(source='application.id', read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = ['id', 'uuid', 'application_id', 'path', 'metadata', 'source_type']
