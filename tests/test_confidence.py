import pytest
from src.domain.confidence import ConfidenceEngine
from src.domain.decision_contract import AIResponse, ActionType, MessageType

@pytest.fixture
def engine():
    return ConfidenceEngine()

@pytest.fixture
def sample_ai_resp():
    return AIResponse(
        action=ActionType.notify,
        message_type=MessageType.personal,
        reason="Looks important",
        confidence=0.9,
        evidence_message_ids=["msg_old_1"]
    )

def test_confidence_calculation_high(engine, sample_ai_resp):
    rule_output = {"suggested_action": "notify"}
    features = {"sender_trust": 0.9, "business_trust": 0.8, "group_priority": 1.0}
    hist = [{"message_id": "msg_old_1", "_relevance_score": 4.5}]

    score = engine.calculate(sample_ai_resp, rule_output, features, hist)
    assert 0.8 <= score <= 1.0

def test_confidence_calculation_low(engine):
    # None AI response, low trust
    rule_output = {"suggested_action": "block"}
    features = {"sender_trust": 0.1, "business_trust": 0.0, "group_priority": 0.0}
    hist = []

    score = engine.calculate(None, rule_output, features, hist)
    assert 0.0 <= score <= 0.6

def test_confidence_normalization_bounds(engine, sample_ai_resp):
    score = engine.calculate(sample_ai_resp, {}, {}, [])
    assert 0.0 <= score <= 1.0
