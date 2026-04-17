import pytest
from rest_framework import serializers

from core.models import KnowledgeBase
from core.serializers.knowledge_base import (
    CrawlingConfigSerializer,
    KnowledgeBaseItemSerializer,
    KnowledgeBaseCreateSerializer,
    KnowledgeBaseViewSerializer,
    CrawlingEnableSerializer,
    CrawlingStatsSerializer,
    CrawledPageSerializer,
    CrawlingDataSerializer,
)
from core.tests.factories import UserFactory, ApplicationFactory


@pytest.mark.unit
class TestCrawlingConfigSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = CrawlingConfigSerializer()
        expected_fields = ['max_depth', 'max_pages', 'enable_crawling']
        for field in expected_fields:
            assert field in serializer.fields

    def test_max_depth_is_read_only(self):
        serializer = CrawlingConfigSerializer()
        assert serializer.fields['max_depth'].read_only

    def test_max_pages_is_read_only(self):
        serializer = CrawlingConfigSerializer()
        assert serializer.fields['max_pages'].read_only

    def test_enable_crawling_is_not_read_only(self):
        serializer = CrawlingConfigSerializer()
        assert not serializer.fields['enable_crawling'].read_only

    def test_default_values(self):
        serializer = CrawlingConfigSerializer()
        assert serializer.fields['max_depth'].default == 1
        assert serializer.fields['max_pages'].default == 50


@pytest.mark.unit
class TestKnowledgeBaseItemSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = KnowledgeBaseItemSerializer()
        expected_fields = ['type', 'value', 'file', 'crawling_config']
        for field in expected_fields:
            assert field in serializer.fields

    def test_type_has_correct_choices(self):
        serializer = KnowledgeBaseItemSerializer()
        assert set(serializer.fields['type'].choices.keys()) == {'file', 'text', 'url'}

    def test_value_is_optional(self):
        serializer = KnowledgeBaseItemSerializer()
        assert not serializer.fields['value'].required
        assert serializer.fields['value'].allow_null

    def test_file_is_optional(self):
        serializer = KnowledgeBaseItemSerializer()
        assert not serializer.fields['file'].required
        assert serializer.fields['file'].allow_null

    def test_validate_file_type_with_value(self):
        data = {
            'type': 'file',
            'value': 'test_value'
        }
        serializer = KnowledgeBaseItemSerializer(data=data)
        assert serializer.is_valid()

    def test_validate_file_type_without_value_or_file(self):
        data = {
            'type': 'file'
        }
        serializer = KnowledgeBaseItemSerializer(data=data)
        assert not serializer.is_valid()
        assert 'file' in serializer.errors

    def test_validate_text_type_with_value(self):
        data = {
            'type': 'text',
            'value': 'test_text'
        }
        serializer = KnowledgeBaseItemSerializer(data=data)
        assert serializer.is_valid()

    def test_validate_text_type_without_value(self):
        data = {
            'type': 'text'
        }
        serializer = KnowledgeBaseItemSerializer(data=data)
        assert not serializer.is_valid()
        assert 'value' in serializer.errors

    def test_validate_url_type_with_value(self):
        data = {
            'type': 'url',
            'value': 'https://example.com'
        }
        serializer = KnowledgeBaseItemSerializer(data=data)
        assert serializer.is_valid()

    def test_validate_url_type_without_value(self):
        data = {
            'type': 'url'
        }
        serializer = KnowledgeBaseItemSerializer(data=data)
        assert not serializer.is_valid()
        assert 'value' in serializer.errors


@pytest.mark.unit
class TestKnowledgeBaseCreateSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = KnowledgeBaseCreateSerializer()
        expected_fields = ['items']
        for field in expected_fields:
            assert field in serializer.fields

    def test_items_is_many(self):
        serializer = KnowledgeBaseCreateSerializer()
        assert serializer.fields['items'].many

    def test_create_returns_validated_data(self):
        data = {
            'items': [
                {'type': 'text', 'value': 'test'}
            ]
        }
        serializer = KnowledgeBaseCreateSerializer(data=data)
        assert serializer.is_valid()
        result = serializer.save()
        assert result == data


@pytest.mark.unit
class TestKnowledgeBaseViewSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(application=application)

        serializer = KnowledgeBaseViewSerializer(kb)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'application_id', 'path', 'metadata', 'source_type', 'status', 'created_at',
                          'crawling_enabled', 'crawling_status', 'crawled_pages', 'crawling_config']
        for field in expected_fields:
            assert field in data

    def test_get_crawling_enabled_for_url_with_crawling_enabled(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(
            application=application,
            source_type='url',
            metadata={'crawling_enabled': True}
        )

        serializer = KnowledgeBaseViewSerializer(kb)
        result = serializer.get_crawling_enabled(kb)

        assert result is True

    def test_get_crawling_enabled_for_url_without_crawling_enabled(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(
            application=application,
            source_type='url',
            metadata={}
        )

        serializer = KnowledgeBaseViewSerializer(kb)
        result = serializer.get_crawling_enabled(kb)

        assert result is False

    def test_get_crawling_enabled_for_non_url(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(
            application=application,
            source_type='file'
        )

        serializer = KnowledgeBaseViewSerializer(kb)
        result = serializer.get_crawling_enabled(kb)

        assert result is False

    def test_get_crawling_status_for_url(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(
            application=application,
            source_type='url',
            metadata={'crawling_status': 'in_progress'}
        )

        serializer = KnowledgeBaseViewSerializer(kb)
        result = serializer.get_crawling_status(kb)

        assert result == 'in_progress'

    def test_get_crawling_status_for_non_url(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(
            application=application,
            source_type='file'
        )

        serializer = KnowledgeBaseViewSerializer(kb)
        result = serializer.get_crawling_status(kb)

        assert result is None

    def test_get_crawled_pages_for_url(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(
            application=application,
            source_type='url',
            metadata={'crawled_data': {'total_pages': 10}}
        )

        serializer = KnowledgeBaseViewSerializer(kb)
        result = serializer.get_crawled_pages(kb)

        assert result == 10

    def test_get_crawled_pages_for_non_url(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(
            application=application,
            source_type='file'
        )

        serializer = KnowledgeBaseViewSerializer(kb)
        result = serializer.get_crawled_pages(kb)

        assert result == 0

    def test_get_crawling_config_for_url(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(
            application=application,
            source_type='url',
            metadata={'crawling_config': {'max_depth': 2}}
        )

        serializer = KnowledgeBaseViewSerializer(kb)
        result = serializer.get_crawling_config(kb)

        assert result == {'max_depth': 2}

    def test_get_crawling_config_for_non_url(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        kb = KnowledgeBase.objects.create(
            application=application,
            source_type='file'
        )

        serializer = KnowledgeBaseViewSerializer(kb)
        result = serializer.get_crawling_config(kb)

        assert result == {}


@pytest.mark.unit
class TestCrawlingEnableSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = CrawlingEnableSerializer()
        expected_fields = ['max_depth', 'max_pages']
        for field in expected_fields:
            assert field in serializer.fields

    def test_max_depth_is_read_only(self):
        serializer = CrawlingEnableSerializer()
        assert serializer.fields['max_depth'].read_only

    def test_max_pages_is_read_only(self):
        serializer = CrawlingEnableSerializer()
        assert serializer.fields['max_pages'].read_only

    def test_default_values(self):
        serializer = CrawlingEnableSerializer()
        assert serializer.fields['max_depth'].default == 1
        assert serializer.fields['max_pages'].default == 50


@pytest.mark.unit
class TestCrawlingStatsSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = CrawlingStatsSerializer()
        expected_fields = ['total_pages', 'total_urls_visited', 'total_urls_encountered', 'success_rate',
                          'max_depth_reached', 'deduplication_stats', 'relationship_stats']
        for field in expected_fields:
            assert field in serializer.fields

    def test_all_fields_are_required(self):
        serializer = CrawlingStatsSerializer()
        for field_name, field in serializer.fields.items():
            assert field.required


@pytest.mark.unit
class TestCrawledPageSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = CrawledPageSerializer()
        expected_fields = ['url', 'title', 'description', 'content_length', 'depth', 'status_code',
                          'content_type', 'parent_url', 'retry_attempts']
        for field in expected_fields:
            assert field in serializer.fields

    def test_url_is_required(self):
        serializer = CrawledPageSerializer()
        assert serializer.fields['url'].required

    def test_title_is_optional(self):
        serializer = CrawledPageSerializer()
        assert serializer.fields['title'].allow_null

    def test_description_is_optional(self):
        serializer = CrawledPageSerializer()
        assert serializer.fields['description'].allow_null

    def test_content_type_is_optional(self):
        serializer = CrawledPageSerializer()
        assert serializer.fields['content_type'].allow_null

    def test_parent_url_is_optional(self):
        serializer = CrawledPageSerializer()
        assert serializer.fields['parent_url'].allow_null

    def test_retry_attempts_has_default(self):
        serializer = CrawledPageSerializer()
        assert serializer.fields['retry_attempts'].default == 0


@pytest.mark.unit
class TestCrawlingDataSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = CrawlingDataSerializer()
        expected_fields = ['total_pages', 'pages', 'crawl_stats']
        for field in expected_fields:
            assert field in serializer.fields

    def test_total_pages_is_required(self):
        serializer = CrawlingDataSerializer()
        assert serializer.fields['total_pages'].required

    def test_pages_is_many(self):
        serializer = CrawlingDataSerializer()
        assert serializer.fields['pages'].many

    def test_crawl_stats_is_required(self):
        serializer = CrawlingDataSerializer()
        assert serializer.fields['crawl_stats'].required
