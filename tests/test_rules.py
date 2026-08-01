import pytest
from src.domain.rules import RuleEngine

@pytest.fixture
def engine():
    return RuleEngine()

def test_urgent_family(engine):
    features = {"contains_family": True, "contains_emergency": True}
    context = {"message": {"message_text": "Hospital now"}}
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "notify"
    assert result["rule_name"] == "urgent_family"

def test_admin_announcements(engine):
    features = {}
    context = {
        "message": {"conversation_type": "group"},
        "group_membership": {"role": "admin"}
    }
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "notify"
    assert result["rule_name"] == "admin_announcement"

def test_lottery_scam(engine):
    features = {"contains_lottery": True}
    context = {"message": {"message_text": "You won the lottery!"}}
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "block"
    assert result["rule_name"] == "lottery_scam"

def test_crypto_scam(engine):
    features = {}
    context = {"message": {"message_text": "Send bitcoin to my wallet seed"}}
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "block"
    assert result["rule_name"] == "crypto_scam"

def test_investment_scam(engine):
    features = {}
    context = {"message": {"message_text": "Guaranteed return on invest"}}
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "block"
    assert result["rule_name"] == "investment_scam"

def test_unknown_payment(engine):
    features = {"contains_payment": True, "sender_trust": 0.2}
    context = {"message": {"message_text": "pay me now"}}
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "block"
    assert result["rule_name"] == "unknown_payment"

def test_otp_request(engine):
    features = {"contains_otp": True}
    context = {"message": {"message_text": "Your OTP is 123456"}}
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "notify"
    assert result["rule_name"] == "otp_request"

def test_repeated_promotion(engine):
    features = {"contains_promotion": True, "notification_load": 5}
    context = {"message": {"message_text": "sale today"}}
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "mute"
    assert result["rule_name"] == "repeated_promotion"

def test_muted_group(engine):
    features = {}
    context = {
        "message": {"conversation_type": "group", "message_text": "hello"},
        "group_membership": {"is_muted": True, "role": "member"}
    }
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "mute"
    assert result["rule_name"] == "muted_group"

def test_default_allow(engine):
    features = {"sender_trust": 0.9}
    context = {"message": {"message_text": "hello how are you"}}
    result = engine.evaluate(features, context)
    assert result["suggested_action"] == "allow"
    assert result["rule_name"] == "default_allow"
