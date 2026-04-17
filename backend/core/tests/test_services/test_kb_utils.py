import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from core.services.kb_utils import (
    create_kb_records,
    parse_kb_from_request,
    format_text_uri
)


@pytest.mark.unit
class TestFormatTextUri:
    def test_format_text_uri(self):
        result = format_text_uri("This is a test text value")

        assert result == "text://This is a test text value"

    def test_format_text_uri_long_text(self):
        long_text = "A" * 100
        result = format_text_uri(long_text)

        assert result == f"text://{'A' * 50}"
        assert len(result) == len("text://") + 50

    def test_format_text_uri_empty_string(self):
        result = format_text_uri("")

        assert result == "text://"


@pytest.mark.unit
class TestCreateKBRecords:
    @patch('core.services.kb_utils.KnowledgeBase')
    @patch('core.services.kb_utils.default_storage')
    def test_create_kb_records_file_type(self, mock_storage, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_file = Mock()
        mock_file.name = "test_file.txt"

        mock_storage.save.return_value = "saved_test_file.txt"
        mock_kb_instance = Mock()
        mock_kb_class.return_value = mock_kb_instance
        mock_kb_class.objects.bulk_create = Mock()
        mock_kb_class.objects.filter.return_value.order_by.return_value.__getitem__ = Mock(side_effect=lambda x: [Mock()])

        items = [
            {
                'type': 'file',
                'file': mock_file
            }
        ]

        result = create_kb_records(mock_app, items)

        mock_storage.save.assert_called_once_with("test_file.txt", mock_file)
        mock_kb_class.objects.bulk_create.assert_called_once()

    @patch('core.services.kb_utils.KnowledgeBase')
    def test_create_kb_records_text_type(self, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_kb_instance = Mock()
        mock_kb_class.return_value = mock_kb_instance
        mock_kb_class.objects.bulk_create = Mock()
        mock_kb_class.objects.filter.return_value.order_by.return_value.__getitem__ = Mock(side_effect=lambda x: [Mock()])

        items = [
            {
                'type': 'text',
                'value': 'Test text content'
            }
        ]

        result = create_kb_records(mock_app, items)

        mock_kb_class.objects.bulk_create.assert_called_once()

    @patch('core.services.kb_utils.KnowledgeBase')
    def test_create_kb_records_url_type(self, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_kb_instance = Mock()
        mock_kb_class.return_value = mock_kb_instance
        mock_kb_class.objects.bulk_create = Mock()
        mock_kb_class.objects.filter.return_value.order_by.return_value.__getitem__ = Mock(side_effect=lambda x: [Mock()])

        items = [
            {
                'type': 'url',
                'value': 'https://example.com'
            }
        ]

        result = create_kb_records(mock_app, items)

        mock_kb_class.objects.bulk_create.assert_called_once()

    @patch('core.services.kb_utils.KnowledgeBase')
    def test_create_kb_records_url_with_crawling_config(self, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_kb_instance = Mock()
        mock_kb_class.return_value = mock_kb_instance
        mock_kb_class.objects.bulk_create = Mock()
        mock_kb_class.objects.filter.return_value.order_by.return_value.__getitem__ = Mock(side_effect=lambda x: [Mock()])

        items = [
            {
                'type': 'url',
                'value': 'https://example.com',
                'crawling_config': {
                    'enable_crawling': True,
                    'max_depth': 3,
                    'max_pages': 100
                }
            }
        ]

        result = create_kb_records(mock_app, items)

        mock_kb_class.objects.bulk_create.assert_called_once()

    @patch('core.services.kb_utils.KnowledgeBase')
    @patch('core.services.kb_utils.default_storage')
    def test_create_kb_records_multiple_items(self, mock_storage, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_file = Mock()
        mock_file.name = "test_file.txt"
        mock_storage.save.return_value = "saved_test_file.txt"

        mock_kb_instance = Mock()
        mock_kb_class.return_value = mock_kb_instance
        mock_kb_class.objects.bulk_create = Mock()
        mock_kb_class.objects.filter.return_value.order_by.return_value.__getitem__ = Mock(side_effect=lambda x: [Mock(), Mock()])

        items = [
            {
                'type': 'text',
                'value': 'Test text'
            },
            {
                'type': 'url',
                'value': 'https://example.com'
            }
        ]

        result = create_kb_records(mock_app, items)

        assert mock_kb_class.call_count == 2

    @patch('core.services.kb_utils.KnowledgeBase')
    @patch('core.services.kb_utils.default_storage')
    def test_create_kb_records_file_without_file(self, mock_storage, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_kb_instance = Mock()
        mock_kb_class.return_value = mock_kb_instance
        mock_kb_class.objects.bulk_create = Mock()
        mock_kb_class.objects.filter.return_value.order_by.return_value.__getitem__ = Mock(side_effect=lambda x: [])

        items = [
            {
                'type': 'file',
                'file': None
            }
        ]

        result = create_kb_records(mock_app, items)

        assert mock_kb_class.call_count == 0

    @patch('core.services.kb_utils.KnowledgeBase')
    def test_create_kb_records_empty_items(self, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_kb_class.objects.bulk_create = Mock()
        mock_kb_class.objects.filter.return_value.order_by.return_value.__getitem__ = Mock(side_effect=lambda x: [])

        items = []

        result = create_kb_records(mock_app, items)

        mock_kb_class.objects.bulk_create.assert_called_once_with([])


@pytest.mark.unit
class TestParseKBFromRequest:
    def test_parse_kb_from_request_text_item(self):
        mock_request = Mock()
        mock_request.data = {
            'items[0].type': 'text',
            'items[0].value': 'Test text content'
        }
        mock_request.FILES = {}

        result = parse_kb_from_request(mock_request)

        assert len(result) == 1
        assert result[0]['type'] == 'text'
        assert result[0]['value'] == 'Test text content'

    def test_parse_kb_from_request_url_item(self):
        mock_request = Mock()
        mock_request.data = {
            'items[0].type': 'url',
            'items[0].value': 'https://example.com'
        }
        mock_request.FILES = {}

        result = parse_kb_from_request(mock_request)

        assert len(result) == 1
        assert result[0]['type'] == 'url'
        assert result[0]['value'] == 'https://example.com'
        assert result[0]['crawling_config'] is None

    def test_parse_kb_from_request_url_with_crawling(self):
        mock_request = Mock()
        mock_request.data = {
            'items[0].type': 'url',
            'items[0].value': 'https://example.com',
            'items[0].crawling_config.enable_crawling': 'true',
            'items[0].crawling_config.max_depth': '3',
            'items[0].crawling_config.max_pages': '100'
        }
        mock_request.FILES = {}

        result = parse_kb_from_request(mock_request)

        assert len(result) == 1
        assert result[0]['type'] == 'url'
        assert result[0]['crawling_config']['enable_crawling'] is True
        assert result[0]['crawling_config']['max_depth'] == 3
        assert result[0]['crawling_config']['max_pages'] == 100

    def test_parse_kb_from_request_file_item(self):
        mock_request = Mock()
        mock_request.data = {
            'items[0].type': 'file',
            'items[0].value': ''
        }
        mock_file = Mock()
        mock_file.name = 'test_file.txt'
        mock_request.FILES = {
            'items[0].file': mock_file
        }

        result = parse_kb_from_request(mock_request)

        assert len(result) == 1
        assert result[0]['type'] == 'file'
        assert result[0]['file'] == mock_file

    def test_parse_kb_from_request_multiple_items(self):
        mock_request = Mock()
        mock_request.data = {
            'items[0].type': 'text',
            'items[0].value': 'Test text',
            'items[1].type': 'url',
            'items[1].value': 'https://example.com'
        }
        mock_request.FILES = {}

        result = parse_kb_from_request(mock_request)

        assert len(result) == 2
        assert result[0]['type'] == 'text'
        assert result[1]['type'] == 'url'

    def test_parse_kb_from_request_empty(self):
        mock_request = Mock()
        mock_request.data = {}
        mock_request.FILES = {}

        result = parse_kb_from_request(mock_request)

        assert result == []

    def test_parse_kb_from_request_url_crawling_disabled(self):
        mock_request = Mock()
        mock_request.data = {
            'items[0].type': 'url',
            'items[0].value': 'https://example.com',
            'items[0].crawling_config.enable_crawling': 'false'
        }
        mock_request.FILES = {}

        result = parse_kb_from_request(mock_request)

        assert len(result) == 1
        assert result[0]['crawling_config'] is None

    def test_parse_kb_from_request_url_crawling_defaults(self):
        mock_request = Mock()
        mock_request.data = {
            'items[0].type': 'url',
            'items[0].value': 'https://example.com',
            'items[0].crawling_config.enable_crawling': 'true'
        }
        mock_request.FILES = {}

        result = parse_kb_from_request(mock_request)

        assert len(result) == 1
        assert result[0]['crawling_config']['enable_crawling'] is True
        assert result[0]['crawling_config']['max_depth'] == 1  # default
        assert result[0]['crawling_config']['max_pages'] == 50  # default
