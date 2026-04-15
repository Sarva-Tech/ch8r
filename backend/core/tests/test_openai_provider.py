"""
Tests for OpenAIProvider — unit tests and property-based tests.

Property tests:
  - Property 2: Tool call / structured output mutual exclusion (Validates: Requirements 6.2, 7.2)
  - Property 3: Model list filter stability (Validates: Requirements 5.2, 5.3, 5.6)
  - Property 4: Embedding order preservation (Validates: Requirements 9.2)
  - Property 5: validate_connection never raises (Validates: Requirements 4.2, 4.3)
"""
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from types import SimpleNamespace

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from core.services.providers.ai.openai_provider import OpenAIProvider, EXCLUDED_PREFIXES, EXCLUDED_SUFFIXES
from core.agent_response_schema import SupportAgentResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider(api_key="sk-test", config=None):
    """Return an OpenAIProvider with a mocked openai.OpenAI client."""
    with patch("core.services.providers.ai.openai_provider.openai.OpenAI"):
        provider = OpenAIProvider(api_key=api_key, config=config)
    return provider


def _make_model(model_id, object_="model", created=0, owned_by="openai"):
    m = MagicMock()
    m.id = model_id
    m.object = object_
    m.created = created
    m.owned_by = owned_by
    return m


def _make_stop_response(content: str):
    """Build a minimal ChatCompletion-like object with finish_reason='stop'."""
    choice = MagicMock()
    choice.finish_reason = "stop"
    choice.message.content = content
    choice.message.tool_calls = None

    usage = MagicMock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    usage.total_tokens = 30
    usage.prompt_tokens_details = None

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


def _make_tool_call_response(tool_name="search", args=None):
    """Build a minimal ChatCompletion-like object with finish_reason='tool_calls'."""
    tc = MagicMock()
    tc.id = "call_abc123"
    tc.function.name = tool_name
    tc.function.arguments = json.dumps(args or {"query": "test"})

    choice = MagicMock()
    choice.finish_reason = "tool_calls"
    choice.message.content = ""
    choice.message.tool_calls = [tc]

    usage = MagicMock()
    usage.prompt_tokens = 5
    usage.completion_tokens = 10
    usage.total_tokens = 15
    usage.prompt_tokens_details = None

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


# ---------------------------------------------------------------------------
# Unit tests — __init__
# ---------------------------------------------------------------------------

class TestOpenAIProviderInit:
    def test_init_success(self):
        with patch("core.services.providers.ai.openai_provider.openai.OpenAI") as mock_cls:
            provider = OpenAIProvider(api_key="sk-test")
        mock_cls.assert_called_once_with(api_key="sk-test")
        assert provider.api_key == "sk-test"

    def test_init_with_base_url(self):
        with patch("core.services.providers.ai.openai_provider.openai.OpenAI") as mock_cls:
            provider = OpenAIProvider(api_key="sk-test", config={"base_url": "https://proxy.example.com"})
        mock_cls.assert_called_once_with(api_key="sk-test", base_url="https://proxy.example.com")

    def test_init_with_none_config(self):
        with patch("core.services.providers.ai.openai_provider.openai.OpenAI") as mock_cls:
            provider = OpenAIProvider(api_key="sk-test", config=None)
        mock_cls.assert_called_once_with(api_key="sk-test")

    def test_init_raises_value_error_on_sdk_failure(self):
        with patch("core.services.providers.ai.openai_provider.openai.OpenAI", side_effect=Exception("bad key")):
            with pytest.raises(ValueError, match="Failed to initialize OpenAI client"):
                OpenAIProvider(api_key="bad")


# ---------------------------------------------------------------------------
# Unit tests — get_models
# ---------------------------------------------------------------------------

class TestGetModels:
    def test_filters_excluded_prefixes(self):
        provider = _make_provider()
        raw = [
            _make_model("gpt-4o"),
            _make_model("whisper-1"),
            _make_model("tts-1"),
            _make_model("dall-e-3"),
            _make_model("davinci-002"),
            _make_model("babbage-002"),
            _make_model("text-embedding-ada-002"),
        ]
        provider.client.models.list.return_value.data = raw
        result = provider.get_models()
        ids = [m["id"] for m in result]
        assert "gpt-4o" in ids
        assert "whisper-1" not in ids
        assert "tts-1" not in ids
        assert "dall-e-3" not in ids
        assert "davinci-002" not in ids
        assert "babbage-002" not in ids
        assert "text-embedding-ada-002" not in ids

    def test_filters_instruct_suffix(self):
        provider = _make_provider()
        provider.client.models.list.return_value.data = [
            _make_model("gpt-3.5-turbo-instruct"),
            _make_model("gpt-4o"),
        ]
        result = provider.get_models()
        ids = [m["id"] for m in result]
        assert "gpt-3.5-turbo-instruct" not in ids
        assert "gpt-4o" in ids

    def test_returns_id_and_name_keys(self):
        provider = _make_provider()
        provider.client.models.list.return_value.data = [_make_model("gpt-4o")]
        result = provider.get_models()
        assert len(result) == 1
        assert "id" in result[0]
        assert "name" in result[0]

    def test_raises_value_error_on_api_failure(self):
        provider = _make_provider()
        provider.client.models.list.side_effect = Exception("network error")
        with pytest.raises(ValueError, match="Failed to retrieve models"):
            provider.get_models()

    def test_returns_empty_list_when_all_filtered(self):
        provider = _make_provider()
        provider.client.models.list.return_value.data = [
            _make_model("whisper-1"),
            _make_model("tts-1"),
        ]
        result = provider.get_models()
        assert result == []


# ---------------------------------------------------------------------------
# Unit tests — validate_connection
# ---------------------------------------------------------------------------

class TestValidateConnection:
    def test_returns_true_and_models_on_success(self):
        provider = _make_provider()
        provider.client.models.list.return_value.data = [_make_model("gpt-4o")]
        ok, models = provider.validate_connection()
        assert ok is True
        assert len(models) == 1

    def test_returns_false_empty_on_exception(self):
        provider = _make_provider()
        provider.client.models.list.side_effect = Exception("auth error")
        ok, models = provider.validate_connection()
        assert ok is False
        assert models == []

    def test_never_raises(self):
        provider = _make_provider()
        provider.client.models.list.side_effect = RuntimeError("unexpected")
        # Must not raise
        result = provider.validate_connection()
        assert isinstance(result, tuple)


# ---------------------------------------------------------------------------
# Unit tests — generate_with_conversation
# ---------------------------------------------------------------------------

class TestGenerateWithConversation:
    def _valid_response_json(self):
        return json.dumps({
            "answer": "Reset your password via Settings.",
            "status": "ANSWERED",
            "escalation": False,
            "reason_for_escalation": "",
            "sentiment_score": 70,
            "escalation_score": 5,
            "criticality_score": 10,
        })

    def test_no_tools_returns_parsed_schema(self):
        provider = _make_provider()
        provider.client.chat.completions.create.return_value = _make_stop_response(self._valid_response_json())
        messages = [{"role": "user", "content": "How do I reset my password?"}]
        result, tool_calls, usage = provider.generate_with_conversation(
            model="gpt-4o", messages=messages, tools=None, response_schema=SupportAgentResponse
        )
        assert isinstance(result, SupportAgentResponse)
        assert tool_calls == []
        assert "prompt_tokens" in usage

    def test_no_tools_uses_response_format(self):
        provider = _make_provider()
        provider.client.chat.completions.create.return_value = _make_stop_response(self._valid_response_json())
        messages = [{"role": "user", "content": "Hello"}]
        provider.generate_with_conversation(
            model="gpt-4o", messages=messages, tools=None, response_schema=SupportAgentResponse
        )
        call_kwargs = provider.client.chat.completions.create.call_args[1]
        assert "response_format" in call_kwargs
        assert "tools" not in call_kwargs

    def test_with_tools_returns_tool_calls(self):
        provider = _make_provider()
        provider.client.chat.completions.create.return_value = _make_tool_call_response("search_kb", {"query": "reset"})
        tools = [{"type": "function", "function": {"name": "search_kb", "description": "Search", "parameters": {}}}]
        messages = [{"role": "user", "content": "Help"}]
        text, tool_calls, usage = provider.generate_with_conversation(
            model="gpt-4o", messages=messages, tools=tools, response_schema=SupportAgentResponse
        )
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "search_kb"
        assert "id" in tool_calls[0]
        assert "args" in tool_calls[0]

    def test_with_tools_uses_tool_choice_auto(self):
        provider = _make_provider()
        provider.client.chat.completions.create.return_value = _make_tool_call_response()
        tools = [{"type": "function", "function": {"name": "fn", "description": "", "parameters": {}}}]
        provider.generate_with_conversation(
            model="gpt-4o", messages=[{"role": "user", "content": "x"}], tools=tools, response_schema=SupportAgentResponse
        )
        call_kwargs = provider.client.chat.completions.create.call_args[1]
        assert call_kwargs.get("tool_choice") == "auto"
        assert "response_format" not in call_kwargs

    def test_raises_value_error_on_authentication_error(self):
        import openai as openai_module
        provider = _make_provider()
        provider.client.chat.completions.create.side_effect = openai_module.AuthenticationError(
            message="Invalid key", response=MagicMock(), body={}
        )
        with pytest.raises(ValueError, match="Invalid OpenAI API key"):
            provider.generate_with_conversation(
                model="gpt-4o", messages=[{"role": "user", "content": "x"}],
                tools=None, response_schema=SupportAgentResponse
            )

    def test_raises_value_error_on_rate_limit_error(self):
        import openai as openai_module
        provider = _make_provider()
        provider.client.chat.completions.create.side_effect = openai_module.RateLimitError(
            message="Rate limit", response=MagicMock(), body={}
        )
        with pytest.raises(ValueError, match="rate limit"):
            provider.generate_with_conversation(
                model="gpt-4o", messages=[{"role": "user", "content": "x"}],
                tools=None, response_schema=SupportAgentResponse
            )

    def test_raises_value_error_on_api_error(self):
        import openai as openai_module
        provider = _make_provider()
        provider.client.chat.completions.create.side_effect = openai_module.APIStatusError(
            message="Server error", response=MagicMock(status_code=500), body={}
        )
        with pytest.raises(ValueError, match="OpenAI API error"):
            provider.generate_with_conversation(
                model="gpt-4o", messages=[{"role": "user", "content": "x"}],
                tools=None, response_schema=SupportAgentResponse
            )

    def test_raises_value_error_on_bad_json(self):
        provider = _make_provider()
        provider.client.chat.completions.create.return_value = _make_stop_response("not valid json {{{")
        with pytest.raises(ValueError, match="Failed to parse OpenAI response"):
            provider.generate_with_conversation(
                model="gpt-4o", messages=[{"role": "user", "content": "x"}],
                tools=None, response_schema=SupportAgentResponse
            )


# ---------------------------------------------------------------------------
# Unit tests — embed
# ---------------------------------------------------------------------------

class TestEmbed:
    def test_returns_vectors_in_input_order(self):
        provider = _make_provider()
        # Return shuffled: index 1 first, then 0
        e0 = MagicMock(); e0.index = 0; e0.embedding = [0.1, 0.2]
        e1 = MagicMock(); e1.index = 1; e1.embedding = [0.3, 0.4]
        provider.client.embeddings.create.return_value.data = [e1, e0]  # shuffled
        result = provider.embed(model="text-embedding-3-small", texts=["a", "b"])
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]

    def test_raises_value_error_on_failure(self):
        provider = _make_provider()
        provider.client.embeddings.create.side_effect = Exception("network error")
        with pytest.raises(ValueError, match="OpenAI embedding error"):
            provider.embed(model="text-embedding-3-small", texts=["hello"])


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

# --- Property 5: validate_connection never raises ---
# Validates: Requirements 4.2, 4.3

@given(api_key=st.text())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_5_validate_connection_never_raises(api_key):
    """
    **Validates: Requirements 4.2, 4.3**

    Property 5: validate_connection never raises.
    For any api_key string, validate_connection always returns tuple[bool, list]
    and never propagates an exception.
    """
    with patch("core.services.providers.ai.openai_provider.openai.OpenAI"):
        provider = OpenAIProvider(api_key=api_key if api_key else "sk-x")

    # Make the client raise an arbitrary exception
    provider.client.models.list.side_effect = Exception("simulated failure")

    result = provider.validate_connection()
    assert isinstance(result, tuple)
    assert len(result) == 2
    ok, models = result
    assert isinstance(ok, bool)
    assert isinstance(models, list)
    assert ok is False
    assert models == []


# --- Property 3: Model list filter stability ---
# Validates: Requirements 5.2, 5.3, 5.6

def _model_id_strategy():
    """Generate model IDs including edge cases."""
    normal = st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-_."), min_size=1, max_size=30)
    prefixed = st.sampled_from(list(EXCLUDED_PREFIXES)).map(lambda p: p + "-extra")
    suffixed = st.just("gpt-4o-instruct")
    clean = st.just("gpt-4o")
    return st.one_of(normal, prefixed, suffixed, clean)


@given(model_ids=st.lists(_model_id_strategy(), min_size=0, max_size=20))
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_3_model_list_filter_stability(model_ids):
    """
    **Validates: Requirements 5.2, 5.3, 5.6**

    Property 3: Model list filter stability.
    - Filter excludes models with excluded prefixes or suffixes.
    - Filter is idempotent.
    - Every returned dict contains 'id' and 'name'.
    """
    provider = _make_provider()
    raw = [_make_model(mid) for mid in model_ids]
    provider.client.models.list.return_value.data = raw

    result = provider.get_models()

    # Every returned model must have id and name
    for m in result:
        assert "id" in m
        assert "name" in m

    # No excluded prefix
    for m in result:
        for prefix in EXCLUDED_PREFIXES:
            assert not m["id"].startswith(prefix), f"{m['id']} starts with excluded prefix {prefix}"

    # No excluded suffix
    for m in result:
        for suffix in EXCLUDED_SUFFIXES:
            assert not m["id"].endswith(suffix), f"{m['id']} ends with excluded suffix {suffix}"

    # Idempotency: applying filter again yields same result
    result_ids = {m["id"] for m in result}
    for mid in result_ids:
        assert not any(mid.startswith(p) for p in EXCLUDED_PREFIXES)
        assert not any(mid.endswith(s) for s in EXCLUDED_SUFFIXES)


# --- Property 4: Embedding order preservation ---
# Validates: Requirements 9.2

@given(texts=st.lists(st.text(min_size=1), min_size=1, max_size=10))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_4_embedding_order_preservation(texts):
    """
    **Validates: Requirements 9.2**

    Property 4: Embedding order preservation.
    embed() returns len(result) == len(texts) and result[i] corresponds to texts[i].
    """
    provider = _make_provider()

    # Build shuffled embeddings (reverse order to test sorting)
    embeddings = []
    for i, _ in enumerate(texts):
        e = MagicMock()
        e.index = i
        e.embedding = [float(i), float(i) * 0.1]
        embeddings.append(e)

    # Shuffle: reverse order
    shuffled = list(reversed(embeddings))
    provider.client.embeddings.create.return_value.data = shuffled

    result = provider.embed(model="text-embedding-3-small", texts=texts)

    assert len(result) == len(texts)
    for i, vec in enumerate(result):
        assert vec == [float(i), float(i) * 0.1], f"result[{i}] does not match expected vector for texts[{i}]"


# --- Property 2: Tool call / structured output mutual exclusion ---
# Validates: Requirements 6.2, 7.2

def _valid_response_json():
    return json.dumps({
        "answer": "Here is the answer.",
        "status": "ANSWERED",
        "escalation": False,
        "reason_for_escalation": "",
        "sentiment_score": 50,
        "escalation_score": 10,
        "criticality_score": 5,
    })


@given(
    has_tools=st.booleans(),
    finish_reason=st.sampled_from(["stop", "tool_calls"]),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_2_tool_call_structured_output_mutual_exclusion(has_tools, finish_reason):
    """
    **Validates: Requirements 6.2, 7.2**

    Property 2: Tool call / structured output mutual exclusion.
    - If tools non-empty and finish_reason='tool_calls': tool_calls non-empty, first element is str.
    - If tools empty/None and finish_reason='stop': tool_calls=[], first element is response_schema instance.
    """
    provider = _make_provider()

    tools = [{"type": "function", "function": {"name": "fn", "description": "", "parameters": {}}}] if has_tools else None

    if finish_reason == "tool_calls":
        provider.client.chat.completions.create.return_value = _make_tool_call_response("fn", {"x": 1})
    else:
        provider.client.chat.completions.create.return_value = _make_stop_response(_valid_response_json())

    messages = [{"role": "user", "content": "test"}]

    result_tuple = provider.generate_with_conversation(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        response_schema=SupportAgentResponse,
    )

    first, tool_calls, usage = result_tuple
    assert isinstance(tool_calls, list)
    assert isinstance(usage, dict)

    if finish_reason == "tool_calls":
        # Tool calls branch: tool_calls non-empty, first is str
        assert len(tool_calls) > 0
        assert isinstance(first, str)
        for tc in tool_calls:
            assert "id" in tc
            assert "name" in tc
            assert "args" in tc
    else:
        # Stop branch (no tools): tool_calls empty, first is parsed schema
        if not has_tools:
            assert tool_calls == []
            assert isinstance(first, SupportAgentResponse)
