import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from core.services.ingestion import (
    chunk_text,
    embed_text,
    embed_sparse,
    get_chunks,
    ingest_kb,
    delete_vectors_from_qdrant,
    _extract_content,
    _clean_content,
    _generate_embeddings,
    _cleanup_existing_chunks,
    _upsert_chunks_to_qdrant,
    _finalize_ingestion,
    _handle_duplicate_checks
)


@pytest.mark.unit
class TestChunkText:
    def test_chunk_text_basic(self):
        text = "This is a test text that should be chunked into smaller pieces"
        chunks = chunk_text(text, chunk_size=20, overlap=5)

        assert len(chunks) > 1
        assert all(len(chunk) <= 20 for chunk in chunks)

    def test_chunk_text_shorter_than_chunk_size(self):
        text = "Short text"
        chunks = chunk_text(text, chunk_size=100, overlap=10)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_empty_string(self):
        chunks = chunk_text("", chunk_size=100, overlap=10)

        assert chunks == []

    def test_chunk_text_default_parameters(self):
        text = "A" * 400
        chunks = chunk_text(text)

        assert len(chunks) > 1
        assert all(len(chunk) <= 300 for chunk in chunks)


@pytest.mark.unit
class TestEmbedText:
    @patch('core.services.ingestion._generate_single_embedding')
    @patch('core.models.content_hash.ContentHash')
    def test_embed_text_with_cache(self, mock_content_hash, mock_generate_embedding):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_hash_instance = Mock()
        mock_hash_instance.embedding = [0.1, 0.2, 0.3]
        mock_content_hash.objects.get.return_value = mock_hash_instance
        mock_generate_embedding.return_value = [0.4, 0.5, 0.6]

        chunks = ["chunk1", "chunk2"]
        result = embed_text(chunks, mock_app)

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]

    @patch('core.services.ingestion._generate_single_embedding')
    @patch('core.models.content_hash.ContentHash')
    def test_embed_text_without_cache(self, mock_content_hash, mock_generate_embedding):
        class MockDoesNotExist(Exception):
            pass
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_content_hash.DoesNotExist = MockDoesNotExist
        mock_content_hash.objects.get.side_effect = MockDoesNotExist
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]

        chunks = ["chunk1"]
        result = embed_text(chunks, mock_app)

        assert len(result) == 1
        assert result[0] == [0.1, 0.2, 0.3]
        mock_content_hash.objects.update_or_create.assert_called_once()

    @patch('core.services.ingestion._generate_single_embedding')
    @patch('core.models.content_hash.ContentHash')
    def test_embed_text_empty_embedding(self, mock_content_hash, mock_generate_embedding):
        class MockDoesNotExist(Exception):
            pass
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_content_hash.DoesNotExist = MockDoesNotExist
        mock_content_hash.objects.get.side_effect = MockDoesNotExist
        mock_generate_embedding.return_value = []

        chunks = ["chunk1"]
        result = embed_text(chunks, mock_app)

        assert len(result) == 1
        assert result[0] == []


@pytest.mark.unit
class TestEmbedSparse:
    @patch('core.services.ingestion._get_sparse_model')
    def test_embed_sparse_success(self, mock_get_model):
        mock_model = Mock()
        mock_embedding = Mock()
        mock_embedding.indices.tolist.return_value = [0, 1, 2]
        mock_embedding.values.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model.embed.return_value = [mock_embedding]
        mock_get_model.return_value = mock_model

        chunks = ["chunk1", "chunk2"]
        result = embed_sparse(chunks)

        assert len(result) == 1
        assert result[0].indices == [0, 1, 2]
        assert result[0].values == [0.1, 0.2, 0.3]

    @patch('core.services.ingestion._get_sparse_model')
    def test_embed_sparse_multiple_chunks(self, mock_get_model):
        mock_model = Mock()
        mock_embedding1 = Mock()
        mock_embedding1.indices.tolist.return_value = [0, 1]
        mock_embedding1.values.tolist.return_value = [0.1, 0.2]
        mock_embedding2 = Mock()
        mock_embedding2.indices.tolist.return_value = [2, 3]
        mock_embedding2.values.tolist.return_value = [0.3, 0.4]
        mock_model.embed.return_value = [mock_embedding1, mock_embedding2]
        mock_get_model.return_value = mock_model

        chunks = ["chunk1", "chunk2"]
        result = embed_sparse(chunks)

        assert len(result) == 2


@pytest.mark.unit
class TestExtractContent:
    def test_extract_content_success(self):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.metadata = {'content': 'Test content'}

        result = _extract_content(mock_kb)

        assert result == 'Test content'

    def test_extract_content_no_content(self):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.metadata = {}

        result = _extract_content(mock_kb)

        assert result is None

    def test_extract_content_empty_content(self):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.metadata = {'content': ''}

        result = _extract_content(mock_kb)

        assert result is None


@pytest.mark.unit
class TestCleanContent:
    @patch('core.services.ingestion._quality_filter')
    def test_clean_content_success(self, mock_quality_filter):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'
        mock_kb.status = 'pending'

        mock_quality_filter.should_ingest.return_value = True
        mock_quality_filter.remove_emojis.return_value = 'Cleaned content'

        result = _clean_content('Original content', mock_kb)

        assert result == 'Cleaned content'

    @patch('core.services.ingestion._quality_filter')
    def test_clean_content_filtered(self, mock_quality_filter):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'
        mock_kb.status = 'pending'

        mock_quality_filter.should_ingest.return_value = False

        result = _clean_content('Original content', mock_kb)

        assert result is None
        assert mock_kb.status == 'completed'

    @patch('core.services.ingestion._quality_filter')
    def test_clean_content_empty_after_cleaning(self, mock_quality_filter):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'
        mock_kb.status = 'pending'

        mock_quality_filter.should_ingest.return_value = True
        mock_quality_filter.remove_emojis.return_value = ''

        result = _clean_content('Original content', mock_kb)

        assert result is None
        assert mock_kb.status == 'completed'


@pytest.mark.unit
class TestHandleDuplicateChecks:
    @patch('core.services.ingestion._duplicate_detector')
    def test_handle_duplicate_checks_url_source(self, mock_detector):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'url'
        mock_kb.status = 'pending'
        mock_app = Mock()

        result = _handle_duplicate_checks('content', mock_kb, mock_app)

        assert result is True

    @patch('core.services.ingestion._duplicate_detector')
    def test_handle_duplicate_checks_is_duplicate(self, mock_detector):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'
        mock_kb.status = 'pending'
        mock_app = Mock()

        mock_detector.is_duplicate.return_value = True

        result = _handle_duplicate_checks('content', mock_kb, mock_app)

        assert result is False
        assert mock_kb.status == 'duplicate'

    @patch('core.services.ingestion._duplicate_detector')
    def test_handle_duplicate_checks_semantic_duplicate(self, mock_detector):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'
        mock_kb.status = 'pending'
        mock_app = Mock()

        mock_detector.is_duplicate.return_value = False
        mock_detector.handle_semantic_duplicate.return_value = False
        mock_detector._was_replacement_triggered.return_value = False

        result = _handle_duplicate_checks('content', mock_kb, mock_app)

        assert result is False
        assert mock_kb.status == 'duplicate'

    @patch('core.services.ingestion._duplicate_detector')
    def test_handle_duplicate_checks_replacement_triggered(self, mock_detector):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'
        mock_kb.status = 'pending'
        mock_app = Mock()

        mock_detector.is_duplicate.return_value = False
        mock_detector.handle_semantic_duplicate.return_value = False
        mock_detector._was_replacement_triggered.return_value = True

        result = _handle_duplicate_checks('content', mock_kb, mock_app)

        assert result is False
        mock_kb.delete.assert_called_once()


@pytest.mark.unit
class TestGenerateEmbeddings:
    @patch('core.services.ingestion.embed_text')
    @patch('core.services.ingestion.embed_sparse')
    def test_generate_embeddings_success(self, mock_embed_sparse, mock_embed_text):
        mock_app = Mock()
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()

        mock_embed_text.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_sparse_vector = Mock()
        mock_sparse_vector.indices = [0, 1]
        mock_sparse_vector.values = [0.1, 0.2]
        mock_embed_sparse.return_value = [mock_sparse_vector, mock_sparse_vector]

        chunks = ["chunk1", "chunk2"]
        result = _generate_embeddings(chunks, mock_app, mock_kb)

        assert result is not None
        assert len(result) == 2

    @patch('core.services.ingestion.embed_text')
    @patch('core.services.ingestion.embed_sparse')
    def test_generate_embeddings_all_empty(self, mock_embed_sparse, mock_embed_text):
        mock_app = Mock()
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()

        mock_embed_text.return_value = [[], []]

        chunks = ["chunk1", "chunk2"]
        result = _generate_embeddings(chunks, mock_app, mock_kb)

        assert result is None


@pytest.mark.unit
class TestCleanupExistingChunks:
    @patch('core.services.ingestion.qdrant')
    @patch('core.services.ingestion.IngestedChunk')
    def test_cleanup_existing_chunks(self, mock_chunk_class, mock_qdrant):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()

        mock_chunk1 = Mock()
        mock_chunk1.uuid = uuid.uuid4()
        mock_chunk2 = Mock()
        mock_chunk2.uuid = uuid.uuid4()
        mock_queryset = Mock()
        mock_queryset.__iter__ = Mock(return_value=iter([mock_chunk1, mock_chunk2]))
        mock_queryset.delete = Mock()
        mock_chunk_class.objects.filter.return_value = mock_queryset

        _cleanup_existing_chunks(mock_kb)

        mock_chunk_class.objects.filter.assert_called_once()
        mock_queryset.delete.assert_called_once()


@pytest.mark.unit
class TestFinalizeIngestion:
    @patch('core.services.ingestion._duplicate_detector')
    def test_finalize_ingestion(self, mock_detector):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.status = 'processing'
        mock_kb.source_type = 'text'
        mock_app = Mock()

        _finalize_ingestion(mock_kb, mock_app, 'content', 5, 10)

        assert mock_kb.status == 'completed'
        mock_detector.store_content_hash.assert_called_once()


@pytest.mark.unit
class TestDeleteVectorsFromQdrant:
    @patch('core.services.ingestion.qdrant')
    def test_delete_vectors_empty_ids(self, mock_qdrant):
        delete_vectors_from_qdrant([])

        mock_qdrant.delete.assert_not_called()

    @patch('core.services.ingestion.qdrant')
    def test_delete_vectors_success(self, mock_qdrant):
        ids = ['id1', 'id2']

        delete_vectors_from_qdrant(ids)

        mock_qdrant.delete.assert_called_once()


@pytest.mark.unit
class TestGetChunks:
    @patch('core.services.ingestion.embed_text')
    @patch('core.services.ingestion._get_sparse_model')
    @patch('core.services.ingestion.qdrant')
    @patch('core.services.ingestion.IngestedChunk')
    def test_get_chunks_success(self, mock_chunk_class, mock_qdrant, mock_get_model, mock_embed_text):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_embed_text.return_value = [[0.1, 0.2, 0.3]]

        mock_model = Mock()
        mock_sparse = Mock()
        mock_sparse.indices = [0, 1]
        mock_sparse.values = [0.1, 0.2]
        mock_model.embed.return_value = [mock_sparse]
        mock_get_model.return_value = mock_model

        mock_point = Mock()
        mock_point.id = uuid.uuid4()
        mock_point.score = 0.5
        mock_result = Mock()
        mock_result.points = [mock_point]
        mock_qdrant.query_points.return_value = mock_result

        mock_chunk = Mock()
        mock_chunk.content = 'Test content'
        mock_chunk.chunk_index = 0
        mock_chunk.knowledge_base_id = uuid.uuid4()
        mock_chunk_class.objects.filter.return_value.order_by.return_value = [mock_chunk]

        result = get_chunks('query', mock_app)

        assert len(result) == 1
        assert result[0]['content'] == 'Test content'

    @patch('core.services.ingestion.embed_text')
    def test_get_chunks_empty_embedding(self, mock_embed_text):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_embed_text.return_value = [[]]

        result = get_chunks('query', mock_app)

        assert result == []

    @patch('core.services.ingestion.embed_text')
    @patch('core.services.ingestion._get_sparse_model')
    @patch('core.services.ingestion.qdrant')
    @patch('core.services.ingestion.IngestedChunk')
    def test_get_chunks_low_score(self, mock_chunk_class, mock_qdrant, mock_get_model, mock_embed_text):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_embed_text.return_value = [[0.1, 0.2, 0.3]]

        mock_model = Mock()
        mock_sparse = Mock()
        mock_sparse.indices = [0, 1]
        mock_sparse.values = [0.1, 0.2]
        mock_model.embed.return_value = [mock_sparse]
        mock_get_model.return_value = mock_model

        mock_point = Mock()
        mock_point.id = uuid.uuid4()
        mock_point.score = 0.2
        mock_result = Mock()
        mock_result.points = [mock_point]
        mock_qdrant.query_points.return_value = mock_result

        result = get_chunks('query', mock_app)

        assert result == []


@pytest.mark.unit
class TestIngestKB:
    @patch('core.services.ingestion._finalize_ingestion')
    @patch('core.services.ingestion._upsert_chunks_to_qdrant')
    @patch('core.services.ingestion._cleanup_existing_chunks')
    @patch('core.services.ingestion._generate_embeddings')
    @patch('core.services.ingestion.chunk_text')
    @patch('core.services.ingestion._handle_duplicate_checks')
    @patch('core.services.ingestion._clean_content')
    @patch('core.services.ingestion._extract_content')
    def test_ingest_kb_success(self, mock_extract, mock_clean, mock_duplicate, mock_chunk,
                               mock_generate, mock_cleanup, mock_upsert, mock_finalize):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'
        mock_kb.status = 'pending'
        mock_kb.metadata = {'content': 'Test content'}
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()

        mock_extract.return_value = 'content'
        mock_clean.return_value = 'cleaned content'
        mock_duplicate.return_value = True
        mock_chunk.return_value = ['chunk1', 'chunk2']
        mock_generate.return_value = ([[0.1, 0.2], [0.3, 0.4]], [Mock(), Mock()])
        mock_upsert.return_value = 2

        ingest_kb(mock_kb, mock_app)

        assert mock_finalize.called

    @patch('core.services.ingestion._extract_content')
    def test_ingest_kb_no_content(self, mock_extract):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.metadata = {}
        mock_app = Mock()

        mock_extract.return_value = None

        ingest_kb(mock_kb, mock_app)

        mock_extract.assert_called_once()

    @patch('core.services.ingestion._clean_content')
    @patch('core.services.ingestion._extract_content')
    @patch('core.services.ingestion._handle_duplicate_checks')
    def test_ingest_kb_content_filtered(self, mock_duplicate, mock_extract, mock_clean):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'
        mock_kb.status = 'pending'
        mock_kb.metadata = {'content': 'content'}
        mock_app = Mock()

        mock_extract.return_value = 'content'

        def clean_side_effect(content, kb):
            kb.status = 'completed'
            return None
        mock_clean.side_effect = clean_side_effect

        ingest_kb(mock_kb, mock_app)

        assert mock_kb.status == 'completed'

    @patch('core.services.ingestion._handle_duplicate_checks')
    @patch('core.services.ingestion._clean_content')
    @patch('core.services.ingestion._extract_content')
    def test_ingest_kb_duplicate(self, mock_extract, mock_clean, mock_duplicate):
        mock_kb = Mock()
        mock_kb.uuid = uuid.uuid4()
        mock_kb.source_type = 'text'
        mock_kb.status = 'pending'
        mock_kb.metadata = {'content': 'content'}
        mock_app = Mock()

        mock_extract.return_value = 'content'
        mock_clean.return_value = 'cleaned content'
        mock_duplicate.return_value = False

        ingest_kb(mock_kb, mock_app)

        mock_duplicate.assert_called_once()
