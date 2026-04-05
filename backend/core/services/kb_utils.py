from django.core.files.storage import default_storage
from core.models import KnowledgeBase


def create_kb_records(application, items):
    records = []

    for item in items:
        item_type = item.get('type')

        if item_type == 'file':
            uploaded_file = item.get('file')
            if uploaded_file:
                filename = default_storage.save(uploaded_file.name, uploaded_file)
                records.append(KnowledgeBase(
                    application=application,
                    source_type="file",
                    path=filename,
                    status="pending",
                    metadata={
                        'content': ""
                    }
                ))

        elif item_type == 'text':
            text_value = item.get('value', '')
            path = format_text_uri(text_value)
            records.append(KnowledgeBase(
                application=application,
                source_type="text",
                path=path,
                status="pending",
                metadata={
                    'content': text_value
                }
            ))

        elif item_type == 'url':
            url_value = item.get('value', '')
            crawling_config = item.get('crawling_config', {})

            metadata = {
                'url': url_value,
                'filename': url_value,
                'content': '',
                'extraction_status': 'pending'
            }

            if crawling_config:
                metadata.update({
                    'crawling_enabled': crawling_config.get('enable_crawling', False),
                    'crawling_config': {
                        'max_depth': crawling_config.get('max_depth', 1),
                        'max_pages': crawling_config.get('max_pages', 50),
                        'enabled_at': None
                    }
                })

            records.append(KnowledgeBase(
                application=application,
                source_type="url",
                path=url_value,
                status="pending",
                metadata=metadata
            ))

    KnowledgeBase.objects.bulk_create(records)

    created_kbs = KnowledgeBase.objects.filter(
        application=application
    ).order_by('-id')[:len(records)][::-1]

    return created_kbs


def parse_kb_from_request(request):
    parsed_items = []
    index = 0
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Request data keys: {list(request.data.keys())}")
    logger.info(f"Request FILES keys: {list(request.FILES.keys())}")

    while True:
        type_key = f"items[{index}].type"
        value_key = f"items[{index}].value"
        file_key = f"items[{index}].file"
        crawling_enabled_key = f"items[{index}].crawling_config.enable_crawling"
        crawling_depth_key = f"items[{index}].crawling_config.max_depth"
        crawling_pages_key = f"items[{index}].crawling_config.max_pages"

        if type_key not in request.data:
            break

        item_type = request.data.get(type_key)
        item_value = request.data.get(value_key)
        item_file = request.FILES.get(file_key)

        logger.info(f"Processing item {index}: type={item_type}, value={item_value}, file={item_file}")

        crawling_config = None
        if item_type == 'url':
            crawling_enabled = request.data.get(crawling_enabled_key)
            logger.info(f"Crawling enabled raw: {crawling_enabled}")

            if crawling_enabled == 'true':
                crawling_config = {
                    'enable_crawling': True,
                    'max_depth': int(request.data.get(crawling_depth_key, 1)),
                    'max_pages': int(request.data.get(crawling_pages_key, 50))
                }
                logger.info(f"Crawling config: {crawling_config}")

        parsed_items.append({
            "type": item_type,
            "value": item_value,
            "file": item_file,
            "crawling_config": crawling_config
        })

        index += 1

    logger.info(f"Parsed {len(parsed_items)} items: {parsed_items}")
    return parsed_items

def format_text_uri(text_value: str) -> str:
    return f"text://{text_value[:50]}"
