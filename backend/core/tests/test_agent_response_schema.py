"""
Unit tests for SupportAgentResponse schema.
Requirements: 2.4, 7.6
"""
import pytest
from pydantic import ValidationError

from core.agent_response_schema import ResponseStatus, SupportAgentResponse


def _valid_payload(**overrides):
    base = {
        "answer": "Here is your answer.",
        "status": ResponseStatus.ANSWERED,
        "escalation": False,
        "reason_for_escalation": "",
        "sentiment_score": 50,
        "escalation_score": 10,
        "criticality_score": 20,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Clamping / range tests
# ---------------------------------------------------------------------------

class TestScoreClamping:
    def test_scores_above_100_are_clamped_to_100(self):
        r = SupportAgentResponse(**_valid_payload(sentiment_score=150, escalation_score=200, criticality_score=999))
        assert r.sentiment_score == 100
        assert r.escalation_score == 100
        assert r.criticality_score == 100

    def test_scores_below_0_are_clamped_to_0(self):
        r = SupportAgentResponse(**_valid_payload(sentiment_score=-1, escalation_score=-50, criticality_score=-100))
        assert r.sentiment_score == 0
        assert r.escalation_score == 0
        assert r.criticality_score == 0

    def test_boundary_values_0_and_100_are_accepted(self):
        r = SupportAgentResponse(**_valid_payload(sentiment_score=0, escalation_score=100, criticality_score=0))
        assert r.sentiment_score == 0
        assert r.escalation_score == 100
        assert r.criticality_score == 0

    def test_in_range_values_are_unchanged(self):
        r = SupportAgentResponse(**_valid_payload(sentiment_score=42, escalation_score=77, criticality_score=5))
        assert r.sentiment_score == 42
        assert r.escalation_score == 77
        assert r.criticality_score == 5


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------

class TestSerializationRoundTrip:
    def test_model_dump_contains_all_fields(self):
        r = SupportAgentResponse(**_valid_payload())
        data = r.model_dump()
        assert "answer" in data
        assert "status" in data
        assert "escalation" in data
        assert "reason_for_escalation" in data
        assert "sentiment_score" in data
        assert "escalation_score" in data
        assert "criticality_score" in data

    def test_round_trip_via_json(self):
        original = SupportAgentResponse(**_valid_payload(sentiment_score=72, escalation_score=15, criticality_score=30))
        json_str = original.model_dump_json()
        restored = SupportAgentResponse.model_validate_json(json_str)
        assert restored == original

    def test_round_trip_preserves_clamped_values(self):
        original = SupportAgentResponse(**_valid_payload(sentiment_score=200, escalation_score=-5, criticality_score=50))
        json_str = original.model_dump_json()
        restored = SupportAgentResponse.model_validate_json(json_str)
        assert restored.sentiment_score == 100
        assert restored.escalation_score == 0
        assert restored.criticality_score == 50

    def test_all_response_statuses_round_trip(self):
        for status in ResponseStatus:
            r = SupportAgentResponse(**_valid_payload(status=status))
            data = r.model_dump()
            restored = SupportAgentResponse(**data)
            assert restored.status == status
