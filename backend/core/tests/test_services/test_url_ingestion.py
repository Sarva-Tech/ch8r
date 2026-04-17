import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime

from core.services.url_ingestion import URLIngestionService


@pytest.mark.unit
class TestURLIngestionServiceInit:
    @patch('core.services.url_ingestion.URLExtractor')
    def test_init(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        service = URLIngestionService()

        assert service.extractor == mock_extractor


@pytest.mark.unit
class TestCreateUrlKb:
    @patch('core.models.KnowledgeBase')
    def test_create_url_kb_success(self, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        mock_user = Mock()
        mock_user.uuid = uuid.uuid4()
        url = 'https://example.com'

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.metadata = {}
        mock_kb_class.objects.create.return_value = mock_kb

        service = URLIngestionService()
        result = service.create_url_kb(mock_app, url, mock_user)

        mock_kb_class.objects.create.assert_called_once()
        assert result == mock_kb

    @patch('core.models.KnowledgeBase')
    def test_create_url_kb_with_crawling_config(self, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        mock_user = Mock()
        mock_user.uuid = uuid.uuid4()
        url = 'https://example.com'
        crawling_config = {'enable_crawling': True, 'max_depth': 3, 'max_pages': 50}

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.metadata = {}
        mock_kb_class.objects.create.return_value = mock_kb

        service = URLIngestionService()
        result = service.create_url_kb(mock_app, url, mock_user, crawling_config)

        mock_kb_class.objects.create.assert_called_once()
        assert result == mock_kb

    @patch('core.models.KnowledgeBase')
    def test_create_url_kb_without_crawling_config(self, mock_kb_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        mock_user = Mock()
        mock_user.uuid = uuid.uuid4()
        url = 'https://example.com'

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.metadata = {}
        mock_kb_class.objects.create.return_value = mock_kb

        service = URLIngestionService()
        result = service.create_url_kb(mock_app, url, mock_user, None)

        mock_kb_class.objects.create.assert_called_once()
        assert result == mock_kb


@pytest.mark.unit
class TestExtractUrlContent:
    @patch('core.services.url_ingestion.URLExtractor')
    def test_extract_url_content_success(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor.extract_content.return_value = {
            'url': 'https://example.com',
            'title': 'Example',
            'description': 'Test description',
            'content': 'Test content',
            'links': ['https://example.com/page1'],
            'content_type': 'text/html'
        }
        mock_extractor_class.return_value = mock_extractor

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'url'
        mock_kb.path = 'https://example.com'
        mock_kb.metadata = {}
        mock_kb.updated_at = datetime.now()

        service = URLIngestionService()
        result = service.extract_url_content(mock_kb)

        assert result is True
        assert mock_kb.status == 'processing'
        mock_kb.save.assert_called()

    @patch('core.services.url_ingestion.URLExtractor')
    def test_extract_url_content_not_url_type(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'

        service = URLIngestionService()
        result = service.extract_url_content(mock_kb)

        assert result is False

    @patch('core.services.url_ingestion.URLExtractor')
    def test_extract_url_content_no_path(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'url'
        mock_kb.path = None

        service = URLIngestionService()
        result = service.extract_url_content(mock_kb)

        assert result is False

    @patch('core.services.url_ingestion.URLExtractor')
    def test_extract_url_content_extraction_failed(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor.extract_content.return_value = None
        mock_extractor_class.return_value = mock_extractor

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'url'
        mock_kb.path = 'https://example.com'
        mock_kb.metadata = {}
        mock_kb.updated_at = datetime.now()

        service = URLIngestionService()
        result = service.extract_url_content(mock_kb)

        assert result is False
        assert mock_kb.status == 'failed'

    @patch('core.services.url_ingestion.URLExtractor')
    def test_extract_url_content_exception(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor.extract_content.side_effect = Exception('Network error')
        mock_extractor_class.return_value = mock_extractor

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'url'
        mock_kb.path = 'https://example.com'
        mock_kb.metadata = {}
        mock_kb.updated_at = datetime.now()

        service = URLIngestionService()
        result = service.extract_url_content(mock_kb)

        assert result is False
        assert mock_kb.status == 'failed'


@pytest.mark.unit
class TestEnableCrawlingForKb:
    def test_enable_crawling_for_kb_success(self):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'url'
        mock_kb.metadata = {}
        mock_kb.updated_at = datetime.now()

        service = URLIngestionService()
        service.enable_crawling_for_kb(mock_kb, max_depth=3, max_pages=50)

        assert mock_kb.metadata['crawling_enabled'] is True
        assert mock_kb.metadata['crawling_config']['max_depth'] == 3
        assert mock_kb.metadata['crawling_config']['max_pages'] == 50
        mock_kb.save.assert_called_once()

    def test_enable_crawling_for_kb_not_url_type(self):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'

        service = URLIngestionService()

        with pytest.raises(ValueError, match="Crawling can only be enabled for URL knowledge base items"):
            service.enable_crawling_for_kb(mock_kb)

    def test_enable_crawling_for_kb_default_params(self):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'url'
        mock_kb.metadata = {}
        mock_kb.updated_at = datetime.now()

        service = URLIngestionService()
        service.enable_crawling_for_kb(mock_kb)

        assert mock_kb.metadata['crawling_enabled'] is True
        assert mock_kb.metadata['crawling_config']['max_depth'] == 2
        assert mock_kb.metadata['crawling_config']['max_pages'] == 25


@pytest.mark.unit
class TestDisableCrawlingForKb:
    def test_disable_crawling_for_kb_success(self):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'url'
        mock_kb.metadata = {'crawling_enabled': True, 'crawling_config': {}}
        mock_kb.updated_at = datetime.now()

        service = URLIngestionService()
        service.disable_crawling_for_kb(mock_kb)

        assert mock_kb.metadata['crawling_enabled'] is False
        assert 'disabled_at' in mock_kb.metadata['crawling_config']
        mock_kb.save.assert_called_once()

    def test_disable_crawling_for_kb_not_url_type(self):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'

        service = URLIngestionService()
        service.disable_crawling_for_kb(mock_kb)

        mock_kb.save.assert_not_called()


@pytest.mark.unit
class TestValidateUrlBeforeIngestion:
    @patch('core.services.url_ingestion.URLExtractor')
    def test_validate_url_invalid_format(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor.is_valid_url.return_value = False
        mock_extractor_class.return_value = mock_extractor

        service = URLIngestionService()
        result = service.validate_url_before_ingestion('not-a-url')

        assert result['valid'] is False
        assert 'error' in result

    @patch('core.services.url_ingestion.URLExtractor')
    def test_validate_url_simple_validation(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor.is_valid_url.return_value = True
        mock_extractor_class.return_value = mock_extractor

        service = URLIngestionService()
        result = service.validate_url_before_ingestion('https://example.com', simple_validation=True)

        assert result['valid'] is True
        assert result['message'] == 'URL format is valid. Content will be extracted during processing.'

    @patch('core.services.url_ingestion.URLExtractor')
    def test_validate_url_full_validation_success(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor.is_valid_url.return_value = True
        mock_extractor.extract_content.return_value = {
            'title': 'Example',
            'description': 'Test',
            'content': 'Content',
            'links': [],
            'content_type': 'text/html'
        }
        mock_extractor_class.return_value = mock_extractor

        service = URLIngestionService()
        result = service.validate_url_before_ingestion('https://example.com')

        assert result['valid'] is True
        assert result['title'] == 'Example'

    @patch('core.services.url_ingestion.URLExtractor')
    def test_validate_url_extraction_failed(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor.is_valid_url.return_value = True
        mock_extractor.extract_content.return_value = None
        mock_extractor_class.return_value = mock_extractor

        service = URLIngestionService()
        result = service.validate_url_before_ingestion('https://example.com')

        assert result['valid'] is False
        assert 'error' in result

    @patch('core.services.url_ingestion.URLExtractor')
    def test_validate_url_timeout(self, mock_extractor_class):
        import requests
        mock_extractor = Mock()
        mock_extractor.is_valid_url.return_value = True
        mock_extractor.extract_content.side_effect = requests.exceptions.Timeout()
        mock_extractor_class.return_value = mock_extractor

        service = URLIngestionService()
        result = service.validate_url_before_ingestion('https://example.com')

        assert result['valid'] is False
        assert 'timed out' in result['error']

    @patch('core.services.url_ingestion.URLExtractor')
    def test_validate_url_connection_error(self, mock_extractor_class):
        import requests
        mock_extractor = Mock()
        mock_extractor.is_valid_url.return_value = True
        mock_extractor.extract_content.side_effect = requests.exceptions.ConnectionError()
        mock_extractor_class.return_value = mock_extractor

        service = URLIngestionService()
        result = service.validate_url_before_ingestion('https://example.com')

        assert result['valid'] is False
        assert 'connect' in result['error']

    @patch('core.services.url_ingestion.URLExtractor')
    def test_validate_url_403_error(self, mock_extractor_class):
        import requests
        mock_extractor = Mock()
        mock_extractor.is_valid_url.return_value = True
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.reason = 'Forbidden'
        mock_extractor.extract_content.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_extractor_class.return_value = mock_extractor

        service = URLIngestionService()
        result = service.validate_url_before_ingestion('https://example.com')

        assert result['valid'] is False
        assert '403' in result['error']

    @patch('core.services.url_ingestion.URLExtractor')
    def test_validate_url_404_error(self, mock_extractor_class):
        import requests
        mock_extractor = Mock()
        mock_extractor.is_valid_url.return_value = True
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = 'Not Found'
        mock_extractor.extract_content.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_extractor_class.return_value = mock_extractor

        service = URLIngestionService()
        result = service.validate_url_before_ingestion('https://example.com')

        assert result['valid'] is False
        assert '404' in result['error']


@pytest.mark.unit
class TestReprocessUrl:
    @patch('core.services.url_ingestion.URLExtractor')
    def test_reprocess_url_success(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor.extract_content.return_value = {
            'url': 'https://example.com',
            'title': 'Example',
            'description': 'Test',
            'content': 'Content',
            'links': [],
            'content_type': 'text/html'
        }
        mock_extractor_class.return_value = mock_extractor

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'url'
        mock_kb.path = 'https://example.com'
        mock_kb.metadata = {'extraction_error': 'Previous error'}
        mock_kb.updated_at = datetime.now()

        service = URLIngestionService()
        result = service.reprocess_url(mock_kb)

        assert result is True
        assert 'extraction_error' not in mock_kb.metadata

    @patch('core.services.url_ingestion.URLExtractor')
    def test_reprocess_url_not_url_type(self, mock_extractor_class):
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'

        service = URLIngestionService()
        result = service.reprocess_url(mock_kb)

        assert result is False
