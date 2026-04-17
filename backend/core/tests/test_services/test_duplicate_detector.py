import pytest
from unittest.mock import Mock, patch, MagicMock
from django.core.exceptions import ObjectDoesNotExist

from core.services.duplicate_detector import DuplicateDetector
from core.models.content_hash import ContentHash
from core.models.knowledge_base import KnowledgeBase


@pytest.mark.unit
class TestDuplicateDetector:
    def test_init(self):
        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()

            assert detector._ai_client_service is not None
            assert detector._quality_filter is not None
            assert detector._replacement_triggered is False

    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_get_content_fingerprint(self, mock_generate_hash):
        mock_generate_hash.return_value = 'test_hash_123'

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            result = detector.get_content_fingerprint('test content')

            mock_generate_hash.assert_called_once_with('test content')
            assert result == 'test_hash_123'

    @patch('core.services.duplicate_detector.ContentHash.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_get_embedding_cached(self, mock_generate_hash, mock_get):
        mock_cached_hash = Mock()
        mock_cached_hash.embedding = [0.1, 0.2, 0.3]
        mock_generate_hash.return_value = 'hash123'
        mock_get.return_value = mock_cached_hash

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector._get_embedding('test content', mock_app)

            assert result == [0.1, 0.2, 0.3]
            mock_get.assert_called_once()

    @patch('core.services.duplicate_detector.ContentHash.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.objects.update_or_create')
    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_get_embedding_not_cached(self, mock_generate_hash, mock_update_or_create, mock_get):
        mock_generate_hash.return_value = 'hash123'
        mock_get.side_effect = ContentHash.DoesNotExist()
        mock_update_or_create.return_value = (Mock(), True)

        with patch('core.services.duplicate_detector.AIClientService') as mock_ai_service, \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            mock_provider = Mock()
            mock_provider.embed.return_value = [[0.1, 0.2, 0.3]]
            mock_ai_service.return_value.get_client_and_model.return_value = (mock_provider, 'model')

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector._get_embedding('test content', mock_app)

            assert result == [0.1, 0.2, 0.3]
            mock_update_or_create.assert_called_once()

    @patch('core.services.duplicate_detector.ContentHash.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_get_embedding_no_provider(self, mock_generate_hash, mock_get):
        mock_generate_hash.return_value = 'hash123'
        mock_get.side_effect = ContentHash.DoesNotExist()

        with patch('core.services.duplicate_detector.AIClientService') as mock_ai_service, \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            mock_ai_service.return_value.get_client_and_model.return_value = (None, None)

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector._get_embedding('test content', mock_app)

            assert result is None

    @patch('core.services.duplicate_detector.ContentHash')
    def test_generate_new_embedding_success(self, mock_content_hash):
        mock_content_hash.generate_content_hash.return_value = 'hash123'

        with patch('core.services.duplicate_detector.AIClientService') as mock_ai_service, \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            mock_provider = Mock()
            mock_provider.embed.return_value = [[0.1, 0.2, 0.3]]
            mock_ai_service.return_value.get_client_and_model.return_value = (mock_provider, 'model')

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector._generate_new_embedding('test content', mock_app)

            assert result == [0.1, 0.2, 0.3]

    @patch('core.services.duplicate_detector.ContentHash')
    def test_generate_new_embedding_failure(self, mock_content_hash):
        mock_content_hash.generate_content_hash.return_value = 'hash123'

        with patch('core.services.duplicate_detector.AIClientService') as mock_ai_service, \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            mock_ai_service.return_value.get_client_and_model.side_effect = Exception("API error")

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector._generate_new_embedding('test content', mock_app)

            assert result is None

    def test_cosine_similarity_identical_vectors(self):
        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()

            vec1 = [1.0, 2.0, 3.0]
            vec2 = [1.0, 2.0, 3.0]

            result = detector._cosine_similarity(vec1, vec2)

            assert result == 1.0

    def test_cosine_similarity_orthogonal_vectors(self):
        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()

            vec1 = [1.0, 0.0]
            vec2 = [0.0, 1.0]

            result = detector._cosine_similarity(vec1, vec2)

            assert result == 0.0

    def test_cosine_similarity_empty_vectors(self):
        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()

            result = detector._cosine_similarity([], [])

            assert result == 0.0

    def test_cosine_similarity_mismatched_lengths(self):
        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()

            result = detector._cosine_similarity([1.0, 2.0], [1.0])

            assert result == 0.0


    @patch('core.services.duplicate_detector.ContentHash.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_find_similar_content_no_embedding(self, mock_generate_hash, mock_get):
        mock_generate_hash.return_value = 'hash123'
        mock_get.side_effect = ContentHash.DoesNotExist()

        with patch('core.services.duplicate_detector.AIClientService') as mock_ai_service, \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            mock_ai_service.return_value.get_client_and_model.return_value = (None, None)

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.find_similar_content('test content', mock_app)

            assert result == []

    @patch('core.services.duplicate_detector.KnowledgeBase')
    @patch('core.services.duplicate_detector.ContentHash')
    def test_find_similar_content_empty_content(self, mock_content_hash, mock_kb):
        detector = DuplicateDetector()

        result = detector.find_similar_content('', Mock())

        assert result == []


    @patch('core.services.duplicate_detector.KnowledgeBase.objects.filter')
    @patch('core.services.duplicate_detector.ContentHash.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.objects.update_or_create')
    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_is_semantic_duplicate_no_similar(self, mock_generate_hash, mock_update_or_create, mock_get, mock_kb_filter):
        mock_generate_hash.return_value = 'hash123'
        mock_get.side_effect = ContentHash.DoesNotExist()
        mock_update_or_create.return_value = (Mock(), True)

        mock_kb_filter.return_value.exclude.return_value = []

        with patch('core.services.duplicate_detector.AIClientService') as mock_ai_service, \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            mock_provider = Mock()
            mock_provider.embed.return_value = [[0.1, 0.2, 0.3]]
            mock_ai_service.return_value.get_client_and_model.return_value = (mock_provider, 'model')

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.is_semantic_duplicate('test content', mock_app)

            assert result is False

    @patch('core.services.duplicate_detector.KnowledgeBase')
    @patch('core.services.duplicate_detector.ContentHash')
    def test_should_replace_content_quality_improvement(self, mock_content_hash, mock_kb):
        mock_kb_obj = Mock()
        mock_kb_obj.metadata = {'content': 'old low quality content'}
        mock_kb.objects.get.return_value = mock_kb_obj

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter') as mock_quality:
            mock_quality.return_value.calculate_quality_score.side_effect = [0.8, 0.5]

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.should_replace_content('new high quality content', 'kb-uuid', mock_app)

            assert result is True

    @patch('core.services.duplicate_detector.KnowledgeBase')
    @patch('core.services.duplicate_detector.ContentHash')
    def test_should_replace_content_no_improvement(self, mock_content_hash, mock_kb):
        mock_kb_obj = Mock()
        mock_kb_obj.metadata = {'content': 'old high quality content'}
        mock_kb.objects.get.return_value = mock_kb_obj

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter') as mock_quality:
            mock_quality.return_value.calculate_quality_score.side_effect = [0.5, 0.8]

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.should_replace_content('new low quality content', 'kb-uuid', mock_app)

            assert result is False

    @patch('core.services.duplicate_detector.KnowledgeBase.objects.get')
    def test_should_replace_content_kb_not_found(self, mock_get):
        mock_get.side_effect = KnowledgeBase.DoesNotExist()

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.should_replace_content('new content', 'kb-uuid', mock_app)

            assert result is True

    @patch('core.services.duplicate_detector.KnowledgeBase')
    @patch('core.services.duplicate_detector.ContentHash')
    def test_replace_content_success(self, mock_content_hash, mock_kb):
        mock_kb_obj = Mock()
        mock_kb_obj.metadata = {}
        mock_kb_obj.chunks.all.return_value = []
        mock_kb.objects.get.return_value = mock_kb_obj

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.replace_content('kb-uuid', 'new content', mock_app)

            assert result is True
            mock_kb_obj.save.assert_called_once()

    @patch('core.services.duplicate_detector.KnowledgeBase.objects.get')
    def test_replace_content_kb_not_found(self, mock_get):
        mock_get.side_effect = Exception("DoesNotExist")

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.replace_content('kb-uuid', 'new content', mock_app)

            assert result is False

    def test_cleanup_old_content(self):
        mock_kb_obj = Mock()
        mock_kb_obj.uuid = 'kb-uuid'
        mock_kb_obj.metadata = {'content': 'old content'}
        mock_kb_obj.application = Mock()
        mock_chunks_qs = Mock()
        mock_chunks_qs.delete.return_value = (0, {})
        mock_chunks_qs.__iter__ = Mock(return_value=iter([]))
        mock_kb_obj.chunks.all.return_value = mock_chunks_qs

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'), \
             patch('core.services.ingestion.delete_vectors_from_qdrant'):
            detector = DuplicateDetector()
            detector.remove_content_hash = Mock()

            result = detector._cleanup_old_content(mock_kb_obj)

            assert result is True

    def test_cleanup_old_content_error(self):
        mock_kb_obj = Mock()
        mock_kb_obj.metadata = {}
        mock_kb_obj.chunks.all.side_effect = Exception("Error")

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()

            result = detector._cleanup_old_content(mock_kb_obj)

            assert result is False

    @patch('core.services.duplicate_detector.KnowledgeBase.objects.filter')
    @patch('core.services.duplicate_detector.ContentHash.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.objects.update_or_create')
    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_handle_semantic_duplicate_no_similar(self, mock_generate_hash, mock_update_or_create, mock_get, mock_kb_filter):
        mock_generate_hash.return_value = 'hash123'
        mock_get.side_effect = ContentHash.DoesNotExist()
        mock_update_or_create.return_value = (Mock(), True)

        mock_kb_filter.return_value.exclude.return_value = []

        with patch('core.services.duplicate_detector.AIClientService') as mock_ai_service, \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            mock_provider = Mock()
            mock_provider.embed.return_value = [[0.1, 0.2, 0.3]]
            mock_ai_service.return_value.get_client_and_model.return_value = (mock_provider, 'model')

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.handle_semantic_duplicate('new content', mock_app, 'kb-uuid')

            assert result is True

    @patch('core.services.duplicate_detector.KnowledgeBase.objects.filter')
    @patch('core.services.duplicate_detector.KnowledgeBase.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.objects.update_or_create')
    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_handle_semantic_duplicate_replace(self, mock_generate_hash, mock_update_or_create, mock_get, mock_kb_get, mock_kb_filter):
        mock_generate_hash.return_value = 'hash123'
        mock_get.side_effect = ContentHash.DoesNotExist()
        mock_update_or_create.return_value = (Mock(), True)

        mock_kb_obj = Mock()
        mock_kb_obj.uuid = 'similar-kb-uuid'
        mock_kb_obj.metadata = {'content': 'old content'}
        mock_kb_obj.chunks.all.return_value = []
        mock_kb_filter.return_value.exclude.return_value = [mock_kb_obj]
        mock_kb_get.return_value = mock_kb_obj

        with patch('core.services.duplicate_detector.AIClientService') as mock_ai_service, \
             patch('core.services.duplicate_detector.ContentQualityFilter') as mock_quality, \
             patch('core.services.ingestion.delete_vectors_from_qdrant'):
            mock_provider = Mock()
            mock_provider.embed.side_effect = [[[0.1, 0.2, 0.3]], [[0.1, 0.2, 0.3]]]
            mock_ai_service.return_value.get_client_and_model.return_value = (mock_provider, 'model')
            mock_quality.return_value.calculate_quality_score.side_effect = [0.8, 0.5]

            detector = DuplicateDetector()
            detector.remove_content_hash = Mock()
            mock_app = Mock()

            result = detector.handle_semantic_duplicate('new content', mock_app, 'kb-uuid')

            assert result is False
            assert detector._was_replacement_triggered() is True

    @patch('core.services.duplicate_detector.KnowledgeBase.objects.filter')
    @patch('core.services.duplicate_detector.KnowledgeBase.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.objects.update_or_create')
    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_handle_semantic_duplicate_keep_existing(self, mock_generate_hash, mock_update_or_create, mock_get, mock_kb_get, mock_kb_filter):
        mock_generate_hash.return_value = 'hash123'
        mock_get.side_effect = ContentHash.DoesNotExist()
        mock_update_or_create.return_value = (Mock(), True)

        mock_kb_obj = Mock()
        mock_kb_obj.uuid = 'similar-kb-uuid'
        mock_kb_obj.metadata = {'content': 'high quality content'}
        mock_kb_filter.return_value.exclude.return_value = [mock_kb_obj]
        mock_kb_get.return_value = mock_kb_obj

        with patch('core.services.duplicate_detector.AIClientService') as mock_ai_service, \
             patch('core.services.duplicate_detector.ContentQualityFilter') as mock_quality:
            mock_provider = Mock()
            mock_provider.embed.side_effect = [[[0.1, 0.2, 0.3]], [[0.9, 0.8, 0.7]]]
            mock_ai_service.return_value.get_client_and_model.return_value = (mock_provider, 'model')
            mock_quality.return_value.calculate_quality_score.side_effect = [0.5, 0.8]

            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.handle_semantic_duplicate('new content', mock_app, 'kb-uuid')

            assert result is False
            assert detector._was_replacement_triggered() is False

    @patch('core.services.duplicate_detector.ContentHash')
    def test_is_duplicate(self, mock_content_hash):
        mock_content_hash.generate_content_hash.return_value = 'hash123'
        mock_content_hash.objects.get.return_value = Mock()

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.is_duplicate('test content', mock_app)

            assert result is True

    @patch('core.services.duplicate_detector.ContentHash.objects.get')
    @patch('core.services.duplicate_detector.ContentHash.generate_content_hash')
    def test_is_duplicate_not_found(self, mock_generate_hash, mock_get):
        mock_generate_hash.return_value = 'hash123'
        mock_get.side_effect = ContentHash.DoesNotExist()

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.is_duplicate('test content', mock_app)

            assert result is False

    @patch('core.services.duplicate_detector.ContentHash')
    def test_is_duplicate_empty_content(self, mock_content_hash):
        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()

            result = detector.is_duplicate('', Mock())

            assert result is False

    @patch('core.services.duplicate_detector.ContentHash')
    def test_store_content_hash(self, mock_content_hash):
        mock_content_hash.generate_content_hash.return_value = 'hash123'
        mock_content_hash.objects.create.return_value = Mock()

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.store_content_hash('test content', mock_app)

            assert result is True
            mock_content_hash.objects.create.assert_called_once()

    @patch('core.services.duplicate_detector.ContentHash')
    def test_store_content_hash_empty(self, mock_content_hash):
        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()

            result = detector.store_content_hash('', Mock())

            assert result is False

    @patch('core.services.duplicate_detector.ContentHash')
    def test_remove_content_hash(self, mock_content_hash):
        mock_content_hash.generate_content_hash.return_value = 'hash123'
        mock_content_hash.objects.filter.return_value.delete.return_value = (1, {})

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.remove_content_hash('test content', mock_app)

            assert result is True

    @patch('core.services.duplicate_detector.ContentHash')
    def test_remove_content_hash_not_found(self, mock_content_hash):
        mock_content_hash.generate_content_hash.return_value = 'hash123'
        mock_content_hash.objects.filter.return_value.delete.return_value = (0, {})

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.remove_content_hash('test content', mock_app)

            assert result is False

    @patch('core.services.duplicate_detector.ContentHash')
    def test_get_duplicate_stats(self, mock_content_hash):
        mock_content_hash.objects.filter.return_value.count.return_value = 10
        mock_content_hash.objects.filter.return_value.values_list.return_value.distinct.return_value = ['text', 'file']

        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()
            mock_app = Mock()

            result = detector.get_duplicate_stats(mock_app)

            assert result['total_unique_content'] == 10
            assert 'content_type_breakdown' in result

    @patch('core.services.duplicate_detector.ContentHash')
    def test_get_duplicate_stats_no_app(self, mock_content_hash):
        with patch('core.services.duplicate_detector.AIClientService'), \
             patch('core.services.duplicate_detector.ContentQualityFilter'):
            detector = DuplicateDetector()

            result = detector.get_duplicate_stats(None)

            assert result == {}
