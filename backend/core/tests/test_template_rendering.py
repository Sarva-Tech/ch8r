"""
Tests for default.j2 prompt template rendering.
Validates Requirements 7.1, 7.2, 7.3, 7.4, 7.5
"""
import os

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from jinja2 import Environment, FileSystemLoader

# Resolve template directory relative to this file
TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__),  # backend/core/tests/
    "..", "..", "templates"     # backend/templates/
)
TEMPLATES_DIR = os.path.abspath(TEMPLATES_DIR)


def render_default(product_name="TestProduct", tone="professional", integration_context=""):
    """Helper: render default.j2 with given context."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("prompts/default.j2")
    return template.render(
        product_name=product_name,
        tone=tone,
        integration_context=integration_context,
    )


# ---------------------------------------------------------------------------
# Unit tests — 9.2
# ---------------------------------------------------------------------------

class TestDefaultTemplateSchemaFields:
    """Assert rendered output contains all required SupportAgentResponse field names."""

    def test_answer_field_mentioned(self):
        rendered = render_default()
        assert "answer" in rendered

    def test_status_field_mentioned(self):
        rendered = render_default()
        assert "status" in rendered

    def test_escalation_field_mentioned(self):
        rendered = render_default()
        assert "escalation" in rendered

    def test_reason_for_escalation_field_mentioned(self):
        rendered = render_default()
        assert "reason_for_escalation" in rendered

    def test_sentiment_score_field_mentioned(self):
        rendered = render_default()
        assert "sentiment_score" in rendered

    def test_escalation_score_field_mentioned(self):
        rendered = render_default()
        assert "escalation_score" in rendered

    def test_criticality_score_field_mentioned(self):
        rendered = render_default()
        assert "criticality_score" in rendered

    def test_all_response_status_values_mentioned(self):
        rendered = render_default()
        for status in [
            "ANSWERED",
            "CLARIFICATION_NEEDED",
            "INSUFFICIENT_INFORMATION",
            "ESCALATED",
            "USER_REQUESTED_ESCALATION",
            "POTENTIALLY_IRRELEVANT",
        ]:
            assert status in rendered, f"ResponseStatus value '{status}' not found in template"


class TestDefaultTemplateScoringInstructions:
    """Assert scoring instructions are present (Requirement 7.3)."""

    def test_score_range_0_to_100_mentioned(self):
        rendered = render_default()
        assert "0" in rendered and "100" in rendered

    def test_sentiment_score_guidance_present(self):
        rendered = render_default()
        # Should describe emotional tone
        assert "sentiment" in rendered.lower()
        assert "negative" in rendered.lower()
        assert "positive" in rendered.lower()

    def test_escalation_score_guidance_present(self):
        rendered = render_default()
        assert "escalation_score" in rendered

    def test_criticality_score_guidance_present(self):
        rendered = render_default()
        assert "criticality_score" in rendered
        assert "severity" in rendered.lower()


class TestDefaultTemplateToolCallingGuidance:
    """Assert tool-calling guidance is present (Requirement 7.2)."""

    def test_tool_call_guidance_present(self):
        rendered = render_default()
        assert "tool" in rendered.lower()

    def test_answer_directly_guidance_present(self):
        rendered = render_default()
        assert "answer directly" in rendered.lower() or "directly" in rendered.lower()

    def test_two_shot_awareness_present(self):
        rendered = render_default()
        # Template should mention that tool calls and direct answers are mutually exclusive per shot
        assert "tool call" in rendered.lower() or "call a tool" in rendered.lower()


class TestDefaultTemplateEscalationGuidance:
    """Assert escalation trigger guidance aligned with threshold=70 (Requirement 7.4)."""

    def test_escalation_threshold_70_mentioned(self):
        rendered = render_default()
        assert "70" in rendered

    def test_user_requested_escalation_mentioned(self):
        rendered = render_default()
        assert "USER_REQUESTED_ESCALATION" in rendered

    def test_escalation_bool_field_guidance_present(self):
        rendered = render_default()
        assert "true" in rendered.lower() or "false" in rendered.lower()


class TestDefaultTemplateProductNameAndTone:
    """Assert product_name and tone variables are rendered."""

    def test_product_name_rendered(self):
        rendered = render_default(product_name="AcmeCorp")
        assert "AcmeCorp" in rendered

    def test_tone_rendered(self):
        rendered = render_default(tone="friendly")
        assert "friendly" in rendered


# ---------------------------------------------------------------------------
# Property test — 9.1 (Property 14)
# ---------------------------------------------------------------------------

# Feature: intelligent-chat-pipeline, Property 14: Integration context in rendered template
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(integration_context=st.text(min_size=1, max_size=500).filter(lambda s: s.strip()))
def test_integration_context_in_rendered_template(integration_context):
    """
    Property 14: Integration context in rendered template
    Validates: Requirements 7.5

    For any non-empty integration_context, the rendered prompt must:
    1. Contain the integration_context string.
    2. Include an instruction not to ask the user for connection parameters.
    """
    rendered = render_default(integration_context=integration_context)

    # The context string must appear in the rendered output
    assert integration_context in rendered, (
        f"integration_context not found in rendered template.\n"
        f"Context: {integration_context!r}"
    )

    # The template must instruct the LLM not to ask for connection parameters
    rendered_lower = rendered.lower()
    do_not_ask_instruction = (
        "do not ask" in rendered_lower
        or "not ask" in rendered_lower
        or "do not ask the user" in rendered_lower
    )
    assert do_not_ask_instruction, (
        "Template does not contain 'do not ask' instruction for integration context."
    )


@settings(max_examples=50)
@given(
    product_name=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
    tone=st.sampled_from(["professional", "friendly", "formal", "casual"]),
)
def test_product_name_and_tone_always_rendered(product_name, tone):
    """
    For any product_name and tone, the rendered template must contain both values.
    Validates: Requirements 7.1 (template renders correctly for all products)
    """
    rendered = render_default(product_name=product_name, tone=tone)
    assert product_name in rendered
    assert tone in rendered


def test_no_integration_context_hides_block():
    """When integration_context is empty, the integration block should not appear."""
    rendered = render_default(integration_context="")
    # The pre-configured integrations instruction should not appear
    assert "pre-configured" not in rendered.lower() or "No integrations" in rendered
