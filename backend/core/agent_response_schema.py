from enum import Enum
from pydantic import BaseModel, Field

class ResponseStatus(str, Enum):
    ANSWERED = "ANSWERED"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    ESCALATED = "ESCALATED"
    USER_REQUESTED_ESCALATION = "USER_REQUESTED_ESCALATION"
    POTENTIALLY_IRRELEVANT = "POTENTIALLY_IRRELEVANT"

class SupportAgentResponse(BaseModel):
    answer: str = Field(..., description="The support agent's reply to the user query.")
    status: ResponseStatus = Field(..., description="The result of the response analysis or next step needed.")
    escalation: bool = Field(..., description="Indicates whether the query should be escalated to human support.")
    reason_for_escalation: str = Field(..., description="Optional explanation for escalation. Can be an empty string.")