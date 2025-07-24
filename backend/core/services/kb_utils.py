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
                        'filename': filename,
                        'content': ""
                    }
                ))

        elif item_type == 'text':
            text_value = item.get('value', '')
            path = f"text://{text_value[:50]}"
            records.append(KnowledgeBase(
                application=application,
                source_type="text",
                path=path,
                status="pending",
                metadata={
                    'filename': path,
                    'content': text_value
                }
            ))

        elif item_type == 'url':
            url_value = item.get('value', '')
            records.append(KnowledgeBase(
                application=application,
                source_type="url",
                path=url_value,
                status="pending",
                metadata={
                    'filename': url_value,
                    'content': ''
                }
            ))

    KnowledgeBase.objects.bulk_create(records)

    created_kbs = KnowledgeBase.objects.filter(
        application=application
    ).order_by('-id')[:len(records)][::-1]

    return created_kbs


def parse_kb_from_request(request):
    parsed_items = []
    index = 0

    while True:
        type_key = f"items[{index}].type"
        value_key = f"items[{index}].value"
        file_key = f"items[{index}].file"

        if type_key not in request.data:
            break

        item_type = request.data.get(type_key)
        item_value = request.data.get(value_key)
        item_file = request.FILES.get(file_key)

        parsed_items.append({
            "type": item_type,
            "value": item_value,
            "file": item_file
        })

        index += 1

    return parsed_items
