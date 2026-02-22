---
description: AI/ML integration rules for Ch8r project
trigger: manual
---

# AI/ML Integration Rules

## AI Service Architecture

### Service Abstraction Layer

- Create abstract base classes for AI services
- Implement factory pattern for AI provider selection
- Use dependency injection for testability
- Support multiple AI providers (OpenAI, Google, Ollama)

```python
# Abstract AI service
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class AIService(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate AI response based on prompt and context"""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for given texts"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the AI model"""
        pass
```

### AI Provider Implementation

- Implement concrete classes for each AI provider
- Handle provider-specific API requirements
- Implement proper error handling and retries
- Support model switching and fallback

```python
# OpenAI implementation
class OpenAIService(AIService):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        try:
            messages = self._build_messages(prompt, context)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise AIServiceError(f"Failed to generate response: {e}")
```

## Vector Database Integration

### Qdrant Integration Rules

- Use Qdrant for vector storage and retrieval
- Implement proper collection management
- Use semantic search for knowledge base queries
- Monitor vector database performance

```python
# Vector database service
class VectorDatabaseService:
    def __init__(self, qdrant_client: QdrantClient):
        self.client = qdrant_client

    async def create_collection(self, collection_name: str, vector_size: int = 1536):
        """Create a new collection for vector storage"""
        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )

    async def upsert_vectors(self, collection_name: str, points: List[PointStruct]):
        """Insert or update vectors in the collection"""
        await self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    async def search_similar(self, collection_name: str, query_vector: List[float], limit: int = 5):
        """Search for similar vectors"""
        results = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        return results
```

### Embedding Generation

- Use consistent embedding models
- Implement proper text preprocessing
- Cache embeddings to reduce API calls
- Handle embedding generation failures

```python
# Embedding service
class EmbeddingService:
    def __init__(self, ai_service: AIService, cache_service: CacheService):
        self.ai_service = ai_service
        self.cache = cache_service

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings with caching"""
        embeddings = []

        for text in texts:
            # Check cache first
            cache_key = f"embedding:{hash(text)}"
            cached_embedding = await self.cache.get(cache_key)

            if cached_embedding:
                embeddings.append(cached_embedding)
            else:
                # Generate new embedding
                embedding = await self.ai_service.generate_embeddings([text])
                await self.cache.set(cache_key, embedding[0], ttl=86400)
                embeddings.append(embedding[0])

        return embeddings
```

## Knowledge Base Processing

### Document Processing Rules

- Support multiple document formats (PDF, DOCX, TXT)
- Implement proper text extraction and cleaning
- Use semantic text splitting for better context
- Store document metadata for retrieval

```python
# Document processing service
class DocumentProcessingService:
    def __init__(self, embedding_service: EmbeddingService, vector_db: VectorDatabaseService):
        self.embedding_service = embedding_service
        self.vector_db = vector_db

    async def process_document(self, document_file: UploadedFile, knowledge_base_id: str):
        """Process uploaded document and store in vector database"""
        try:
            # Extract text from document
            text_content = await self.extract_text(document_file)

            # Split text into chunks
            chunks = await self.split_text(text_content)

            # Generate embeddings
            embeddings = await self.embedding_service.get_embeddings(chunks)

            # Store in vector database
            points = self._create_points(chunks, embeddings, document_file.name)
            await self.vector_db.upsert_vectors(f"kb_{knowledge_base_id}", points)

            return {"status": "success", "chunks_processed": len(chunks)}
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise DocumentProcessingError(f"Failed to process document: {e}")
```

### Text Splitting Strategy

- Use semantic text splitting for better context
- Maintain context windows for AI models
- Handle different document types appropriately
- Optimize chunk size for performance

```python
# Text splitting service
class TextSplittingService:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def split_text_semantically(self, text: str) -> List[str]:
        """Split text semantically using AI"""
        # Use AI to identify natural break points
        prompt = f"Split the following text into logical chunks of ~{self.chunk_size} characters, maintaining context:\n\n{text}"

        response = await self.ai_service.generate_response(prompt)
        chunks = self._parse_chunks_from_response(response)

        return chunks

    def split_text_traditionally(self, text: str) -> List[str]:
        """Traditional text splitting by paragraphs and sentences"""
        # Implementation for traditional splitting
        pass
```

## AI Response Generation

### Context Management

- Build relevant context from knowledge base
- Implement proper context ranking and selection
- Use conversation history for context
- Limit context size for model constraints

```python
# Context building service
class ContextBuildingService:
    def __init__(self, vector_db: VectorDatabaseService, embedding_service: EmbeddingService):
        self.vector_db = vector_db
        self.embedding_service = embedding_service

    async def build_context(self, query: str, knowledge_base_id: str, conversation_history: List[Dict] = None) -> str:
        """Build context for AI response generation"""
        # Generate query embedding
        query_embedding = await self.embedding_service.get_embeddings([query])

        # Search for relevant documents
        search_results = await self.vector_db.search_similar(
            f"kb_{knowledge_base_id}",
            query_embedding[0],
            limit=5
        )

        # Build context from search results
        context_parts = []
        for result in search_results:
            context_parts.append(result.payload.get('text', ''))

        # Add conversation history if available
        if conversation_history:
            context_parts.extend([f"Q: {h['question']}\nA: {h['answer']}" for h in conversation_history[-3:]])

        return '\n\n'.join(context_parts)
```

### Response Generation Rules

- Use consistent prompt templates
- Implement proper response formatting
- Add safety filters and content moderation
- Handle edge cases and fallback responses

```python
# Response generation service
class ResponseGenerationService:
    def __init__(self, ai_service: AIService, context_builder: ContextBuildingService):
        self.ai_service = ai_service
        self.context_builder = context_builder

    async def generate_response(self, query: str, knowledge_base_id: str, conversation_history: List[Dict] = None) -> str:
        """Generate AI response with context"""
        try:
            # Build context
            context = await self.context_builder.build_context(query, knowledge_base_id, conversation_history)

            # Build prompt
            prompt = self._build_prompt(query, context)

            # Generate response
            response = await self.ai_service.generate_response(prompt)

            # Filter and validate response
            filtered_response = await self._filter_response(response)

            return filtered_response
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I apologize, but I'm unable to process your request at the moment. Please try again later."
```

## AI Safety and Ethics

### Content Filtering

- Implement input validation and sanitization
- Filter inappropriate content in responses
- Use content moderation APIs
- Implement prompt injection protection

```python
# Content filtering service
class ContentFilteringService:
    def __init__(self):
        self.inappropriate_patterns = [
            r'\b(hate|violence|illegal)\b',
            # Add more patterns
        ]

    async def filter_input(self, text: str) -> str:
        """Filter user input for inappropriate content"""
        # Check for inappropriate patterns
        for pattern in self.inappropriate_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise InappropriateContentError("Input contains inappropriate content")

        return text

    async def filter_output(self, text: str) -> str:
        """Filter AI output for inappropriate content"""
        # Similar filtering for AI responses
        return text
```

### Bias and Fairness

- Monitor AI responses for bias
- Implement fairness checks
- Use diverse training data
- Regular bias audits and assessments

### Transparency and Explainability

- Log AI interactions for debugging
- Provide confidence scores when possible
- Explain AI limitations to users
- Implement human escalation paths

## Performance Optimization

### Caching Strategy

- Cache AI responses to reduce costs
- Cache embeddings for frequently used text
- Use Redis for distributed caching
- Implement cache invalidation strategies

```python
# AI caching service
class AICacheService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def get_cached_response(self, prompt_hash: str) -> Optional[str]:
        """Get cached AI response"""
        return await self.redis.get(f"ai_response:{prompt_hash}")

    async def cache_response(self, prompt_hash: str, response: str, ttl: int = 3600):
        """Cache AI response"""
        await self.redis.setex(f"ai_response:{prompt_hash}", ttl, response)
```

<!-- ### Rate Limiting

- Implement per-user rate limiting
- Use token bucket algorithm
- Monitor AI API usage
- Implement cost optimization strategies -->

## Monitoring and Analytics

### AI Performance Monitoring

- Track response times and accuracy
- Monitor API costs and usage
- Log AI interaction patterns
- Set up performance alerts

### Quality Assurance

- Implement response quality metrics
- Use human evaluation for critical responses
- Monitor user satisfaction scores
- Continuous model improvement

## Error Handling and Resilience

### Fallback Strategies

- Implement multiple AI providers
- Use fallback models for reliability
- Graceful degradation for failures
- Human escalation for critical issues

```python
# Resilient AI service
class ResilientAIService:
    def __init__(self, primary_service: AIService, fallback_service: AIService):
        self.primary = primary_service
        self.fallback = fallback_service

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        try:
            return await self.primary.generate_response(prompt, context)
        except Exception as e:
            logger.warning(f"Primary AI service failed: {e}, trying fallback")
            return await self.fallback.generate_response(prompt, context)
```

### Error Recovery

- Implement retry logic with exponential backoff
- Log all AI service failures
- Monitor error rates and patterns
- Implement circuit breaker patterns
