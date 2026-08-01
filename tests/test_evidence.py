import pytest
from src.domain.evidence import EvidenceEngine
from src.domain.decision_contract import AIResponse, ActionType, MessageType

@pytest.fixture
def engine():
    return EvidenceEngine()

def test_no_fabricated_ids(engine):
    ai_resp = AIResponse(
        action=ActionType.notify,
        message_type=MessageType.personal,
        reason="test",
        confidence=0.9,
        evidence_message_ids=["msg_fake_999", "msg_real_1"]
    )
    hist = [{"message_id": "msg_real_1"}]
    
    valid_ids = engine.extract_evidence_message_ids(ai_resp, hist)
    assert valid_ids == ["msg_real_1"]
    assert "msg_fake_999" not in valid_ids

def test_collect_evidence_structure(engine):
    ai_resp = AIResponse(
        action=ActionType.notify,
        message_type=MessageType.personal,
        reason="test",
        confidence=0.9,
        evidence_message_ids=["msg_1"]
    )
    rule_output = {"rule_name": "crypto_scam", "reason": "scam found"}
    context = {
        "sender": {"user_id": "u_2", "name": "Bob"},
        "group": {"group_id": "g_1", "group_name": "Family"}
    }
    hist = [{"message_id": "msg_1"}]

    ev = engine.collect_evidence(ai_resp, rule_output, context, hist)
    
    types = [item["type"] for item in ev]
    assert "historical_message" in types
    assert "rule_match" in types
    assert "sender_match" in types
    assert "group_match" in types

def test_empty_evidence(engine):
    ev = engine.collect_evidence(None, {}, {}, [])
    assert ev == []
