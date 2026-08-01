import pytest
from src.domain.decision_engine import DecisionEngine, FinalDecision
from src.domain.decision_contract import AIResponse, ActionType, MessageType

@pytest.fixture
def engine():
    return DecisionEngine()

def test_make_decision_ai_flow(engine):
    ai_resp = AIResponse(
        action=ActionType.notify,
        message_type=MessageType.personal,
        reason="Personal greeting",
        confidence=0.95,
        evidence_message_ids=["msg_1"]
    )
    rule_output = {"suggested_action": "allow", "risk_score": 0.0, "rule_name": "default_allow"}
    features = {"sender_trust": 0.9}
    context = {"sender": {"user_id": "u_2"}}
    hist = [{"message_id": "msg_1"}]

    decision = engine.make_decision(ai_resp, rule_output, features, context, hist)
    
    assert isinstance(decision, FinalDecision)
    assert decision.action == "notify"
    assert decision.message_type == "personal"
    assert decision.confidence > 0.5
    assert decision.evidence_message_ids == ["msg_1"]
    assert decision.routing_metadata["rule_name"] == "default_allow"

def test_make_decision_high_risk_rule_override(engine):
    # AI says notify, but rule engine detects high risk scam (risk_score >= 0.8)
    ai_resp = AIResponse(
        action=ActionType.notify,
        message_type=MessageType.personal,
        reason="AI hallucination",
        confidence=0.9,
        evidence_message_ids=[]
    )
    rule_output = {
        "suggested_action": "block",
        "risk_score": 0.9,
        "reason": "Crypto scam detected",
        "rule_name": "crypto_scam"
    }

    decision = engine.make_decision(ai_resp, rule_output, {}, {}, [])
    
    assert decision.action == "mute"
    assert decision.message_type == "scam"
    assert "[Rule Override]" in decision.reason

def test_make_decision_fallback_without_ai(engine):
    rule_output = {
        "suggested_action": "mute",
        "risk_score": 0.6,
        "reason": "Repeated promotion",
        "rule_name": "repeated_promotion"
    }

    decision = engine.make_decision(None, rule_output, {}, {}, [])
    
    assert decision.action == "mute"
    assert "[Fallback Rule Engine]" in decision.reason
