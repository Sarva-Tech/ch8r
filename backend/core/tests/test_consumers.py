"""
Tests for LiveUpdatesConsumer WebSocket consumer.

Covers:
- Task 10.1: Property test — accepts widget_ and dashboard_ prefixed connections (Property 21)
- Task 10.2: Unit test — accepts widget_ prefixed client_id
- Task 10.3: Unit test — accepts dashboard_ prefixed client_id
- Rejects connections with invalid prefixes
"""
import asyncio
import pytest
from unittest.mock import AsyncMock
from hypothesis import given, settings as hyp_settings
import hypothesis.strategies as st

from core.consumers import LiveUpdatesConsumer
from core.consts import LIVE_UPDATES_PREFIX


def make_consumer(client_id: str) -> LiveUpdatesConsumer:
    """Build a LiveUpdatesConsumer instance with a mocked scope and channel layer."""
    consumer = LiveUpdatesConsumer()
    consumer.scope = {
        'url_route': {'kwargs': {'client_id': client_id}},
    }
    consumer.channel_name = f"specific.{client_id}"
    consumer.channel_layer = AsyncMock()
    consumer.channel_layer.group_add = AsyncMock()
    consumer.channel_layer.group_discard = AsyncMock()
    consumer.accept = AsyncMock()
    consumer.close = AsyncMock()
    return consumer


def run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_consumer_accepts_widget_prefixed_client_id():
    """Task 10.2 — LiveUpdatesConsumer accepts connection with widget_ prefixed client_id."""
    client_id = "widget_abc123"
    consumer = make_consumer(client_id)

    run(consumer.connect())

    consumer.accept.assert_awaited_once()
    consumer.close.assert_not_awaited()
    consumer.channel_layer.group_add.assert_awaited_once_with(
        f"{LIVE_UPDATES_PREFIX}_{client_id}",
        consumer.channel_name,
    )


@pytest.mark.unit
def test_consumer_accepts_dashboard_prefixed_client_id():
    """Task 10.3 — LiveUpdatesConsumer accepts connection with dashboard_ prefixed client_id."""
    client_id = "dashboard_42"
    consumer = make_consumer(client_id)

    run(consumer.connect())

    consumer.accept.assert_awaited_once()
    consumer.close.assert_not_awaited()
    consumer.channel_layer.group_add.assert_awaited_once_with(
        f"{LIVE_UPDATES_PREFIX}_{client_id}",
        consumer.channel_name,
    )


@pytest.mark.unit
def test_consumer_rejects_invalid_prefix():
    """LiveUpdatesConsumer rejects connections with an unrecognised prefix."""
    consumer = make_consumer("anon_old-uuid")

    run(consumer.connect())

    consumer.close.assert_awaited_once()
    consumer.accept.assert_not_awaited()
    consumer.channel_layer.group_add.assert_not_awaited()


@pytest.mark.unit
def test_consumer_rejects_empty_client_id():
    """LiveUpdatesConsumer rejects connections with an empty client_id."""
    consumer = make_consumer("")

    run(consumer.connect())

    consumer.close.assert_awaited_once()
    consumer.accept.assert_not_awaited()


# ---------------------------------------------------------------------------
# Property-based test (Property 21)
# ---------------------------------------------------------------------------

@pytest.mark.unit
@given(
    prefix=st.sampled_from(['widget_', 'dashboard_']),
    suffix=st.text(
        min_size=1,
        max_size=64,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_',
        ),
    ),
)
@hyp_settings(max_examples=50)
def test_consumer_accepts_valid_prefixes_property(prefix, suffix):
    """
    Property 21: LiveUpdatesConsumer accepts widget_ and dashboard_ prefixed connections.

    Validates: Requirements 8.5

    For any client identifier starting with widget_ or dashboard_, the consumer
    should accept the WebSocket connection and add it to the correct group.
    """
    client_id = f"{prefix}{suffix}"
    consumer = make_consumer(client_id)

    run(consumer.connect())

    consumer.accept.assert_awaited_once()
    consumer.close.assert_not_awaited()
    consumer.channel_layer.group_add.assert_awaited_once_with(
        f"{LIVE_UPDATES_PREFIX}_{client_id}",
        consumer.channel_name,
    )
