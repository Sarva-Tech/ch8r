from rest_framework import serializers

from core.models import KnowledgeBase

class CrawlingConfigSerializer(serializers.Serializer):
    max_depth = serializers.IntegerField(read_only=True, default=1)
    max_pages = serializers.IntegerField(read_only=True, default=50)
    enable_crawling = serializers.BooleanField(default=False)

class KnowledgeBaseItemSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['file', 'text', 'url'])
    value = serializers.CharField(required=False, allow_null=True)
    file = serializers.FileField(required=False, allow_null=True)
    crawling_config = CrawlingConfigSerializer(required=False, allow_null=True)

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
    crawling_enabled = serializers.SerializerMethodField()
    crawling_status = serializers.SerializerMethodField()
    crawled_pages = serializers.SerializerMethodField()
    crawling_config = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeBase
        fields = ['id', 'uuid', 'application_id', 'path', 'metadata', 'source_type', 'status', 'created_at',
                  'crawling_enabled', 'crawling_status', 'crawled_pages', 'crawling_config']

    def get_crawling_enabled(self, obj):
        if obj.source_type == 'url' and obj.metadata:
            return obj.metadata.get('crawling_enabled', False)
        return False

    def get_crawling_status(self, obj):
        if obj.source_type == 'url' and obj.metadata:
            return obj.metadata.get('crawling_status')
        return None

    def get_crawled_pages(self, obj):
        if obj.source_type == 'url' and obj.metadata:
            crawled_data = obj.metadata.get('crawled_data', {})
            return crawled_data.get('total_pages', 0)
        return 0

    def get_crawling_config(self, obj):
        if obj.source_type == 'url' and obj.metadata:
            return obj.metadata.get('crawling_config', {})
        return {}

class CrawlingEnableSerializer(serializers.Serializer):
    max_depth = serializers.IntegerField(read_only=True, default=1)
    max_pages = serializers.IntegerField(read_only=True, default=50)

class CrawlingStatsSerializer(serializers.Serializer):
    total_pages = serializers.IntegerField()
    total_urls_visited = serializers.IntegerField()
    total_urls_encountered = serializers.IntegerField()
    success_rate = serializers.FloatField()
    max_depth_reached = serializers.IntegerField()
    deduplication_stats = serializers.DictField()
    relationship_stats = serializers.DictField()

class CrawledPageSerializer(serializers.Serializer):
    url = serializers.URLField()
    title = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    content_length = serializers.IntegerField()
    depth = serializers.IntegerField()
    status_code = serializers.IntegerField()
    content_type = serializers.CharField(allow_null=True)
    parent_url = serializers.URLField(allow_null=True)
    retry_attempts = serializers.IntegerField(default=0)

class CrawlingDataSerializer(serializers.Serializer):
    total_pages = serializers.IntegerField()
    pages = CrawledPageSerializer(many=True)
    crawl_stats = CrawlingStatsSerializer()
