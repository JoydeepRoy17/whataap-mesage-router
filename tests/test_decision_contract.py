import pytest
from pydantic import ValidationError
from src.domain.decision_contract import AIResponse, ActionType, MessageType

def test_valid_response():
    resp = AIResponse(
        action="notify",
        message_type="urgent",
        reason="Important meeting update.",
        confidence=0.95,
        evidence_message_ids=["msg_123"]
    )
    assert resp.action == ActionType.notify
    assert resp.message_type == MessageType.urgent
    assert resp.confidence == 0.95

def test_invalid_action():
    with pytest.raises(ValidationError) as exc:
        AIResponse(
            action="destroy", # invalid action
            message_type="personal",
            reason="test reason",
            confidence=0.9,
            evidence_message_ids=[]
        )
    assert "Input should be 'notify', 'digest' or 'mute'" in str(exc.value)

def test_invalid_message_type():
    with pytest.raises(ValidationError) as exc:
        AIResponse(
            action="notify",
            message_type="super_urgent", # invalid type
            reason="test reason",
            confidence=0.9,
            evidence_message_ids=[]
        )
    assert "Input should be 'personal', 'urgent', 'event', 'payment', 'business_update', 'promotion', 'greeting', 'forward', 'spam', 'scam' or 'unknown'" in str(exc.value)

def test_confidence_outside_range():
    with pytest.raises(ValidationError) as exc:
        AIResponse(
            action="notify",
            message_type="personal",
            reason="test",
            confidence=1.5, # > 1.0
            evidence_message_ids=[]
        )
    assert "Confidence must be between 0.0 and 1.0" in str(exc.value)
    
    with pytest.raises(ValidationError) as exc2:
        AIResponse(
            action="notify",
            message_type="personal",
            reason="test",
            confidence=-0.1, # < 0.0
            evidence_message_ids=[]
        )
    assert "Confidence must be between 0.0 and 1.0" in str(exc2.value)

def test_missing_fields():
    with pytest.raises(ValidationError) as exc:
        AIResponse(
            action="notify",
            message_type="personal"
            # Missing reason, confidence, evidence
        )
    assert "Field required" in str(exc.value)

def test_invalid_evidence_format():
    with pytest.raises(ValidationError) as exc:
        AIResponse(
            action="notify",
            message_type="personal",
            reason="test",
            confidence=0.9,
            evidence_message_ids="msg_123" # Should be list, not string
        )
    assert "Input should be a valid list" in str(exc.value)
