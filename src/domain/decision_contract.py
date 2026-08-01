"""
Decision Contract Module
Defines the strongly typed Pydantic models for the AI integration interface.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class ActionType(str, Enum):
    notify = "notify"
    digest = "digest"
    mute = "mute"

class MessageType(str, Enum):
    personal = "personal"
    urgent = "urgent"
    event = "event"
    payment = "payment"
    business_update = "business_update"
    promotion = "promotion"
    greeting = "greeting"
    forward = "forward"
    spam = "spam"
    scam = "scam"
    unknown = "unknown"

class IncomingContext(BaseModel):
    """
    The complete context payload sent to the Gemini AI model.
    """
    message: Dict[str, Any]
    user: Dict[str, Any]
    group: Dict[str, Any]
    business: Dict[str, Any]
    business_history: Dict[str, Any]
    historical_messages: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    notification_summary: Dict[str, Any]
    future_media_summary_placeholder: Optional[Dict[str, Any]] = None
    future_extracted_features_placeholder: Optional[Dict[str, Any]] = None
    future_rule_engine_output_placeholder: Optional[Dict[str, Any]] = None

class AIResponse(BaseModel):
    """
    The required structured response from the Gemini AI model.
    """
    action: ActionType = Field(..., description="The routing action to take.")
    message_type: MessageType = Field(..., description="The classified type of the message.")
    reason: str = Field(..., min_length=1, description="A brief explanation for the decision.")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0.")
    evidence_message_ids: List[str] = Field(..., description="List of historical message IDs supporting the decision.")

    @field_validator('confidence')
    @classmethod
    def check_confidence_range(cls, v: float) -> float:
        """Validates that confidence is strictly between 0 and 1 inclusive."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v
