from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List


class IntentType(str, Enum):
    FEATURE_REQUEST = "feature_request"
    GREETING = "greeting"
    BUG_REPORT = "bug_report"
    FEEDBACK = "feedback"
    TROUBLESHOOTING = "troubleshooting"
    HOW_TOS = "how_tos"
    OTHERS = "others"
    IRRELEVANT = "irrelevant"


class ToolCallDecision(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        json_schema_mode='validation',
    )

    name: str = Field(..., description="Name of the tool to call")
    parameters_json: str = Field(
        default="{}",
        description='JSON string of parameters for the tool call. Use "{}" for empty parameters.'
    )


class IntentClassificationResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        json_schema_mode='validation',
    )

    intent: IntentType = Field(..., description="Classified intent of the user's message")
    tools_to_call: List[ToolCallDecision] = Field(
        default_factory=list,
        description="List of tools to call with their parameters. Empty if no tools needed."
    )
    reasoning: str = Field(..., description="Reasoning for intent classification and tool selection")
    kb_sufficient: bool = Field(
        ...,
        description="Whether the knowledge base context alone is sufficient to answer the query"
    )
    sentiment_score: int = Field(..., description="Emotional tone of the user's message (0 = very negative, 100 = very positive)")
    escalation_score: int = Field(..., description="Likelihood that human escalation is needed (0-100)")
    criticality_score: int = Field(..., description="Severity of the user's reported issue (0-100)")

    @field_validator("sentiment_score", "escalation_score", "criticality_score", mode="before")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, int(v)))
