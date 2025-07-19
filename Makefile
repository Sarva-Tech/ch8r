run-qdrant:
	docker run -p 6333:6333 -p 6334:6334 \
		-v ~/Projects/chatterbox/qdrant_storage:/qdrant/storage:z \
		qdrant/qdrant

run-server:
	cd backend && watchfiles --ignore-paths uploads "daphne config.asgi:application" .

run-celery:
	cd backend && celery -A config worker -l info --pool=solo