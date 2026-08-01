"""
Decision Engine Module
Combines deterministic rules, AI output, confidence scoring, and evidence collection
to produce the final routing decision payload.
"""
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.domain.decision_contract import AIResponse, ActionType, MessageType
from src.domain.confidence import ConfidenceEngine
from src.domain.evidence import EvidenceEngine

logger = logging.getLogger(__name__)


class FinalDecision(BaseModel):
    """
    The final routing decision outcome produced by the DecisionEngine.
    """
    action: str = Field(..., description="Final routing action: notify, digest, mute, block, allow")
    message_type: str = Field(..., description="Classified message type")
    reason: str = Field(..., description="Explanation for the decision")
    confidence: float = Field(..., description="Normalized confidence score between 0.0 and 1.0")
    risk_score: float = Field(..., description="Risk score between 0.0 and 1.0")
    evidence_message_ids: List[str] = Field(default_factory=list, description="Validated list of historical message IDs supporting decision")
    routing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata including rule info, trust, and full evidence")


class DecisionEngine:
    """
    Orchestrates confidence computation, evidence gathering, and rule/AI output merging.
    """

    def __init__(
        self,
        confidence_engine: Optional[ConfidenceEngine] = None,
        evidence_engine: Optional[EvidenceEngine] = None
    ):
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.evidence_engine = evidence_engine or EvidenceEngine()

    def make_decision(
        self,
        ai_response: Optional[AIResponse],
        rule_output: Dict[str, Any],
        features: Dict[str, Any],
        context: Dict[str, Any],
        historical_messages: List[Dict[str, Any]],
    ) -> FinalDecision:
        """
        Merges rule engine evaluation and AI response to make the final routing decision.
        """
        # 1. Calculate combined confidence score
        confidence = self.confidence_engine.calculate(
            ai_response=ai_response,
            rule_output=rule_output,
            features=features,
            historical_messages=historical_messages
        )

        # 2. Extract validated evidence and structured evidence list
        evidence_ids = self.evidence_engine.extract_evidence_message_ids(
            ai_response=ai_response,
            historical_messages=historical_messages
        )
        full_evidence = self.evidence_engine.collect_evidence(
            ai_response=ai_response,
            rule_output=rule_output,
            context=context,
            historical_messages=historical_messages
        )

        # 3. Determine final action, message_type, and reason
        # High-risk deterministic rules (e.g. scams, blocks) override AI output
        rule_action = rule_output.get("suggested_action")
        risk_score = float(rule_output.get("risk_score", 0.0))
        rule_name = rule_output.get("rule_name", "default_allow")

        if rule_action in ["block", "mute"] and risk_score >= 0.8:
            # Deterministic safety rule override
            action = rule_action
            msg_type = "scam" if "scam" in rule_name else ("spam" if "promotion" in rule_name else "unknown")
            reason = f"[Rule Override] {rule_output.get('reason')}"
        elif ai_response:
            # Use AI decision if available and no critical safety override
            action = ai_response.action.value
            msg_type = ai_response.message_type.value
            reason = ai_response.reason
        else:
            # Fallback to Rule Engine output when AI response is unavailable/invalid
            action = rule_action if rule_action else "allow"
            msg_type = "unknown"
            reason = f"[Fallback Rule Engine] {rule_output.get('reason', 'No AI response available')}"

        # 4. Strict HackerRank action mapping (notify, digest, mute only)
        if action == "block":
            action = "mute"
        elif action == "allow":
            if rule_name in ["urgent_family", "admin_announcement", "otp_request"]:
                action = "notify"
            else:
                action = "digest"

        # 4. Construct metadata payload
        routing_metadata = {
            "rule_name": rule_name,
            "rule_suggested_action": rule_action,
            "ai_confidence": ai_response.confidence if ai_response else None,
            "sender_trust": features.get("sender_trust"),
            "business_trust": features.get("business_trust"),
            "group_priority": features.get("group_priority"),
            "evidence_details": full_evidence
        }

        return FinalDecision(
            action=action,
            message_type=msg_type,
            reason=reason,
            confidence=confidence,
            risk_score=risk_score,
            evidence_message_ids=evidence_ids,
            routing_metadata=routing_metadata
        )
