from urllib.parse import urlparse

from core.models.chatroom_client_profile import ChatroomClientProfile


def _get_header(request, key, default=''):
    return (request.headers.get(key) or default).strip()


def get_client_ip(request):
    x_forwarded_for = _get_header(request, 'X-Forwarded-For')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()

    real_ip = _get_header(request, 'X-Real-IP')
    if real_ip:
        return real_ip

    return (request.META.get('REMOTE_ADDR') or '').strip() or None


def get_domain_from_request(request):
    origin = _get_header(request, 'Origin')
    referer = _get_header(request, 'Referer')
    source = origin or referer
    if not source:
        return None
    try:
        return urlparse(source).netloc or None
    except ValueError:
        return None


def parse_browser(user_agent):
    ua = (user_agent or '').lower()
    if not ua:
        return 'unknown'
    if 'edg/' in ua:
        return 'edge'
    if 'opr/' in ua or 'opera' in ua:
        return 'opera'
    if 'chrome/' in ua and 'edg/' not in ua and 'opr/' not in ua:
        return 'chrome'
    if 'safari/' in ua and 'chrome/' not in ua:
        return 'safari'
    if 'firefox/' in ua:
        return 'firefox'
    if 'msie' in ua or 'trident/' in ua:
        return 'internet_explorer'
    return 'unknown'


def parse_device_type(user_agent):
    ua = (user_agent or '').lower()
    if not ua:
        return 'unknown'
    if 'bot' in ua or 'spider' in ua or 'crawl' in ua:
        return 'bot'
    if 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    if 'mobi' in ua or 'android' in ua or 'iphone' in ua:
        return 'mobile'
    return 'desktop'


def build_client_context(request, incoming_metadata):
    metadata = incoming_metadata if isinstance(incoming_metadata, dict) else {}
    nested_ctx = metadata.get('client_context')
    nested_ctx = nested_ctx if isinstance(nested_ctx, dict) else {}

    timezone = (
        nested_ctx.get('timezone')
        or nested_ctx.get('timeZone')
        or metadata.get('timezone')
        or metadata.get('timeZone')
        or _get_header(request, 'X-Timezone')
        or _get_header(request, 'Timezone')
        or None
    )

    region = (
        _get_header(request, 'X-Vercel-IP-Country-Region')
        or _get_header(request, 'X-AppEngine-Region')
        or _get_header(request, 'X-Region')
        or nested_ctx.get('region')
        or metadata.get('region')
        or None
    )
    city = (
        _get_header(request, 'X-Vercel-IP-City')
        or _get_header(request, 'X-AppEngine-City')
        or _get_header(request, 'X-City')
        or nested_ctx.get('city')
        or metadata.get('city')
        or None
    )

    user_agent = (
        nested_ctx.get('user_agent')
        or metadata.get('user_agent')
        or _get_header(request, 'User-Agent')
        or None
    )
    domain = (
        nested_ctx.get('domain')
        or metadata.get('domain')
        or get_domain_from_request(request)
    )
    return {
        'ip': get_client_ip(request),
        'region': region,
        'city': city,
        'browser': parse_browser(user_agent),
        'domain': domain,
        'device_type': parse_device_type(user_agent),
        'timezone': timezone,
        'user_agent': user_agent,
    }


def merge_message_metadata(incoming_metadata, client_context):
    if isinstance(incoming_metadata, dict):
        merged = dict(incoming_metadata)
    else:
        merged = {'raw_metadata': incoming_metadata}

    existing_ctx = merged.get('client_context')
    existing_ctx = existing_ctx if isinstance(existing_ctx, dict) else {}

    normalized_ctx = {
        key: value
        for key, value in client_context.items()
        if value not in (None, '')
    }
    merged['client_context'] = {**existing_ctx, **normalized_ctx}
    return merged


def upsert_chatroom_client_profile(chatroom, sender_identifier, client_context):
    profile, created = ChatroomClientProfile.objects.get_or_create(
        chatroom=chatroom,
        defaults={
            'sender_identifier': sender_identifier,
            'ip_address': client_context.get('ip'),
            'region': client_context.get('region'),
            'city': client_context.get('city'),
            'browser': client_context.get('browser'),
            'domain': client_context.get('domain'),
            'device_type': client_context.get('device_type'),
            'timezone': client_context.get('timezone'),
            'user_agent': client_context.get('user_agent'),
            'metadata': {
                'source': 'send_message',
                'chatroom_name': chatroom.name,
            },
        },
    )

    if created:
        return

    updates = []
    if sender_identifier and profile.sender_identifier != sender_identifier:
        profile.sender_identifier = sender_identifier
        updates.append('sender_identifier')

    field_map = {
        'ip_address': client_context.get('ip'),
        'region': client_context.get('region'),
        'city': client_context.get('city'),
        'browser': client_context.get('browser'),
        'domain': client_context.get('domain'),
        'device_type': client_context.get('device_type'),
        'timezone': client_context.get('timezone'),
        'user_agent': client_context.get('user_agent'),
    }
    for field, value in field_map.items():
        if value not in (None, '') and getattr(profile, field) != value:
            setattr(profile, field, value)
            updates.append(field)

    if updates:
        updates.append('updated_at')
        profile.save(update_fields=updates)
