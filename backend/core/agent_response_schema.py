from enum import Enum
from pydantic import BaseModel, Field, field_validator

class ResponseStatus(str, Enum):
    ANSWERED = "ANSWERED"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    ESCALATED = "ESCALATED"
    USER_REQUESTED_ESCALATION = "USER_REQUESTED_ESCALATION"
    POTENTIALLY_IRRELEVANT = "POTENTIALLY_IRRELEVANT"

class SupportAgentResponse(BaseModel):
    answer: str = Field(
        ...,
        description=(
            "The assistant's response in GitHub Flavored Markdown. "
        )
    )
    status: ResponseStatus = Field(..., description="The result of the response analysis or next step needed.")
    escalation: bool = Field(..., description="Indicates whether the query should be escalated to human support.")
    reason_for_escalation: str = Field(default="", description="Optional explanation for escalation. Can be an empty string.")
    sentiment_score: int = Field(..., description="Emotional tone of the user's message (0 = very negative, 100 = very positive).")
    escalation_score: int = Field(..., description="Likelihood that human escalation is needed (0–100).")
    criticality_score: int = Field(..., description="Severity of the user's reported issue (0–100).")

    @field_validator("reason_for_escalation", mode="before")
    @classmethod
    def default_reason_for_escalation(cls, v):
        if v is None:
            return ""
        return v

    @field_validator("sentiment_score", "escalation_score", "criticality_score", mode="before")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, int(v)))