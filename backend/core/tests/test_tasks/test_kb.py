import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from core.tasks.kb import send_kb_update, get_processor, process_kb_item, process_kb
from core.models.knowledge_base import KBStatus


@pytest.mark.unit
class TestSendKbUpdate:
    @patch('core.tasks.kb.get_channel_layer')
    @patch('core.tasks.kb.async_to_sync')
    def test_send_kb_update_success(self, mock_async_to_sync, mock_get_channel_layer):
        mock_kb = Mock()
        mock_kb.id = 1
        mock_kb.uuid = 'kb-uuid-123'
        mock_kb.application.owner.id = 123

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        def mock_async_to_sync_func(func):
            return func
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        send_kb_update(mock_kb, 'completed')

        mock_async_to_sync.assert_called_once()
        mock_channel_layer.group_send.assert_called_once()

    @patch('core.tasks.kb.get_channel_layer')
    def test_send_kb_update_channel_layer_none(self, mock_get_channel_layer):
        mock_kb = Mock()
        mock_kb.uuid = 'kb-uuid-123'
        mock_get_channel_layer.return_value = None

        send_kb_update(mock_kb, 'completed')

        # Should return early without error
        mock_get_channel_layer.assert_called_once()

    @patch('core.tasks.kb.get_channel_layer')
    @patch('core.tasks.kb.async_to_sync')
    def test_send_kb_update_exception(self, mock_async_to_sync, mock_get_channel_layer):
        mock_kb = Mock()
        mock_kb.uuid = 'kb-uuid-123'
        mock_kb.application.owner.id = 123

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        def mock_async_to_sync_func(func):
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                raise Exception('WebSocket error')
            return wrapper
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        send_kb_update(mock_kb, 'completed')

        mock_channel_layer.group_send.assert_called_once()


@pytest.mark.unit
class TestGetProcessor:
    @patch('core.tasks.kb.FileProcessor')
    @patch('core.tasks.kb.TextProcessor')
    @patch('core.tasks.kb.URLProcessor')
    def test_get_processor_file(self, mock_url_processor, mock_text_processor, mock_file_processor):
        mock_kb = Mock()
        mock_kb.source_type = 'file'

        mock_file_processor_instance = Mock()
        mock_file_processor.return_value = mock_file_processor_instance

        processor = get_processor(mock_kb)

        assert processor == mock_file_processor_instance
        mock_file_processor.assert_called_once()

    @patch('core.tasks.kb.FileProcessor')
    @patch('core.tasks.kb.TextProcessor')
    @patch('core.tasks.kb.URLProcessor')
    def test_get_processor_text(self, mock_url_processor, mock_text_processor, mock_file_processor):
        mock_kb = Mock()
        mock_kb.source_type = 'text'

        mock_text_processor_instance = Mock()
        mock_text_processor.return_value = mock_text_processor_instance

        processor = get_processor(mock_kb)

        assert processor == mock_text_processor_instance
        mock_text_processor.assert_called_once()

    @patch('core.tasks.kb.FileProcessor')
    @patch('core.tasks.kb.TextProcessor')
    @patch('core.tasks.kb.URLProcessor')
    def test_get_processor_url(self, mock_url_processor, mock_text_processor, mock_file_processor):
        mock_kb = Mock()
        mock_kb.source_type = 'url'

        mock_url_processor_instance = Mock()
        mock_url_processor.return_value = mock_url_processor_instance

        processor = get_processor(mock_kb)

        assert processor == mock_url_processor_instance
        mock_url_processor.assert_called_once()

    @patch('core.tasks.kb.FileProcessor')
    @patch('core.tasks.kb.TextProcessor')
    @patch('core.tasks.kb.URLProcessor')
    def test_get_processor_invalid_source_type(self, mock_url_processor, mock_text_processor, mock_file_processor):
        mock_kb = Mock()
        mock_kb.source_type = 'invalid'

        with pytest.raises(ValueError, match='No processor found for source_type'):
            get_processor(mock_kb)


@pytest.mark.unit
class TestProcessKbItem:
    @patch('core.tasks.kb.send_kb_update')
    @patch('core.tasks.kb.get_processor')
    def test_process_kb_item_success(self, mock_get_processor, mock_send_kb_update):
        mock_kb = Mock()
        mock_kb.uuid = 'kb-uuid-123'
        mock_kb.metadata = {}

        mock_processor = Mock()
        mock_processor.process.return_value = True
        mock_get_processor.return_value = mock_processor

        result = process_kb_item(mock_kb)

        assert result is True
        mock_processor.process.assert_called_once_with(mock_kb)

    @patch('core.tasks.kb.send_kb_update')
    @patch('core.tasks.kb.get_processor')
    def test_process_kb_item_processor_failure(self, mock_get_processor, mock_send_kb_update):
        mock_kb = Mock()
        mock_kb.uuid = 'kb-uuid-123'
        mock_kb.metadata = {}

        mock_processor = Mock()
        mock_processor.process.return_value = False
        mock_get_processor.return_value = mock_processor

        result = process_kb_item(mock_kb)

        assert result is False
        mock_processor.process.assert_called_once_with(mock_kb)

    @patch('core.tasks.kb.send_kb_update')
    @patch('core.tasks.kb.get_processor')
    def test_process_kb_item_exception(self, mock_get_processor, mock_send_kb_update):
        mock_kb = Mock()
        mock_kb.uuid = 'kb-uuid-123'
        mock_kb.metadata = {}

        mock_get_processor.side_effect = Exception('Processor error')

        result = process_kb_item(mock_kb)

        assert result is False
        assert mock_kb.status == KBStatus.FAILED
        mock_kb.save.assert_called_once()
        mock_send_kb_update.assert_called_once_with(mock_kb, mock_kb.status)


@pytest.mark.unit
class TestProcessKb:
    @patch('core.tasks.kb.process_kb_item')
    @patch('core.tasks.kb.KnowledgeBase')
    def test_process_kb_success(self, mock_kb_class, mock_process_kb_item):
        mock_kb = Mock()
        mock_kb.uuid = 'kb-uuid-123'
        mock_kb.metadata = {}

        mock_kb_class.objects.filter.return_value.select_related.return_value = [mock_kb]

        process_kb([1])

        mock_process_kb_item.assert_called_once_with(mock_kb)

    @patch('core.tasks.kb.send_kb_update')
    @patch('core.tasks.kb.KnowledgeBase')
    def test_process_kb_exception_handling(self, mock_kb_class, mock_send_kb_update):
        mock_kb = Mock()
        mock_kb.uuid = 'kb-uuid-123'
        mock_kb.metadata = {}

        mock_kb_class.objects.filter.return_value.select_related.return_value = [mock_kb]
        mock_kb_class.DoesNotExist = Exception

        from core.tasks.kb import process_kb_item
        with patch('core.tasks.kb.process_kb_item', side_effect=Exception('Processing error')):
            process_kb([1])

        assert mock_kb.status == KBStatus.FAILED
        mock_kb.save.assert_called_once()
        mock_send_kb_update.assert_called_once_with(mock_kb, mock_kb.status)

    @patch('core.tasks.kb.process_kb_item')
    @patch('core.tasks.kb.KnowledgeBase')
    def test_process_kb_multiple_items(self, mock_kb_class, mock_process_kb_item):
        mock_kb1 = Mock()
        mock_kb1.uuid = 'kb-uuid-123'
        mock_kb1.metadata = {}

        mock_kb2 = Mock()
        mock_kb2.uuid = 'kb-uuid-456'
        mock_kb2.metadata = {}

        mock_kb_class.objects.filter.return_value.select_related.return_value = [mock_kb1, mock_kb2]

        process_kb([1, 2])

        assert mock_process_kb_item.call_count == 2
        mock_process_kb_item.assert_any_call(mock_kb1)
        mock_process_kb_item.assert_any_call(mock_kb2)


@pytest.mark.unit
class TestFileProcessor:
    @patch('core.tasks.kb.extract_text_from_file')
    @patch('core.tasks.kb.send_kb_update')
    def test_file_processor_should_process(self, mock_send_kb_update, mock_extract_text):
        from core.tasks.kb import FileProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'file'

        processor = FileProcessor()
        assert processor.should_process(mock_kb) is True

    @patch('core.tasks.kb.extract_text_from_file')
    @patch('core.tasks.kb.send_kb_update')
    def test_file_processor_should_not_process(self, mock_send_kb_update, mock_extract_text):
        from core.tasks.kb import FileProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'text'

        processor = FileProcessor()
        assert processor.should_process(mock_kb) is False

    @patch('core.tasks.kb.extract_text_from_file')
    @patch('core.tasks.kb.send_kb_update')
    def test_file_processor_extract_content_not_modified(self, mock_send_kb_update, mock_extract_text):
        from core.tasks.kb import FileProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'file'
        mock_kb.metadata = {}
        mock_extract_text.return_value = 'extracted content'

        processor = FileProcessor()
        result = processor.extract_content(mock_kb)

        assert result is True
        mock_extract_text.assert_called_once_with(mock_kb.path)
        assert mock_kb.metadata['content'] == 'extracted content'
        mock_send_kb_update.assert_called_once()

    @patch('core.tasks.kb.extract_text_from_file')
    @patch('core.tasks.kb.send_kb_update')
    def test_file_processor_extract_content_modified(self, mock_send_kb_update, mock_extract_text):
        from core.tasks.kb import FileProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'file'
        mock_kb.metadata = {'is_modified_by_user': True}

        processor = FileProcessor()
        result = processor.extract_content(mock_kb)

        assert result is True
        mock_extract_text.assert_not_called()
        mock_send_kb_update.assert_not_called()


@pytest.mark.unit
class TestTextProcessor:
    @patch('core.tasks.kb.send_kb_update')
    def test_text_processor_should_process(self, mock_send_kb_update):
        from core.tasks.kb import TextProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'text'

        processor = TextProcessor()
        assert processor.should_process(mock_kb) is True

    @patch('core.tasks.kb.send_kb_update')
    def test_text_processor_should_not_process(self, mock_send_kb_update):
        from core.tasks.kb import TextProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'file'

        processor = TextProcessor()
        assert processor.should_process(mock_kb) is False

    @patch('core.tasks.kb.send_kb_update')
    def test_text_processor_extract_content(self, mock_send_kb_update):
        from core.tasks.kb import TextProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'text'

        processor = TextProcessor()
        result = processor.extract_content(mock_kb)

        assert result is True


@pytest.mark.unit
class TestURLProcessor:
    @patch('core.tasks.kb.send_kb_update')
    def test_url_processor_should_process(self, mock_send_kb_update):
        from core.tasks.kb import URLProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'url'

        processor = URLProcessor()
        assert processor.should_process(mock_kb) is True

    @patch('core.tasks.kb.send_kb_update')
    def test_url_processor_should_not_process(self, mock_send_kb_update):
        from core.tasks.kb import URLProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'file'

        processor = URLProcessor()
        assert processor.should_process(mock_kb) is False

    @patch('core.tasks.kb.send_kb_update')
    @patch('core.tasks.kb.URLIngestionService')
    def test_url_processor_extract_content_success(self, mock_url_service_class, mock_send_kb_update):
        from core.tasks.kb import URLProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'url'
        mock_kb.metadata = {}
        mock_kb.path = 'https://example.com'
        mock_kb.updated_at = Mock()

        mock_url_service = Mock()
        mock_url_service.extract_url_content.return_value = True
        mock_url_service_class.return_value = mock_url_service

        processor = URLProcessor()
        result = processor.extract_content(mock_kb)

        assert result is True
        mock_url_service.extract_url_content.assert_called_once_with(mock_kb)

    @patch('core.tasks.kb.send_kb_update')
    @patch('core.tasks.kb.URLIngestionService')
    def test_url_processor_extract_content_failure(self, mock_url_service_class, mock_send_kb_update):
        from core.tasks.kb import URLProcessor

        mock_kb = Mock()
        mock_kb.source_type = 'url'
        mock_kb.metadata = {}

        mock_url_service = Mock()
        mock_url_service.extract_url_content.return_value = False
        mock_url_service_class.return_value = mock_url_service

        processor = URLProcessor()
        result = processor.extract_content(mock_kb)

        assert result is False
