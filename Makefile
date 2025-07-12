run-qdrant:
	docker run -p 6333:6333 -p 6334:6334 \
		-v ~/Projects/chatterbox/qdrant_storage:/qdrant/storage:z \
		qdrant/qdrant
