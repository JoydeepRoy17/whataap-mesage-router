import pytest
from src.domain.features import FeatureExtractor

@pytest.fixture
def extractor():
    return FeatureExtractor()

def test_extract_keywords(extractor):
    context = {
        "message": {
            "message_text": "Please pay the invoice for the lottery you won!",
            "created_at": "2026-08-01 10:00"
        }
    }
    media = {"media_type": "text", "content": "Please pay the invoice for the lottery you won!"}
    
    features = extractor.extract(context, media)
    
    assert features["contains_payment"] is True
    assert features["contains_invoice"] is True
    assert features["contains_lottery"] is True
    assert features["contains_emergency"] is False
    assert features["quiet_hours"] is False

def test_extract_regex(extractor):
    context = {
        "message": {
            "message_text": "Call me at 123-456-7890 or visit https://example.com"
        }
    }
    features = extractor.extract(context, {})
    
    assert features["contains_phone"] is True
    assert features["contains_url"] is True

def test_forwarded_score(extractor):
    context = {
        "message": {
            "forwarded_count": "3"
        }
    }
    features = extractor.extract(context, {})
    assert features["forwarded_score"] == 0.6

    context_high = {
        "message": {
            "forwarded_count": 10
        }
    }
    features_high = extractor.extract(context_high, {})
    assert features_high["forwarded_score"] == 1.0

def test_trust_and_priority(extractor):
    context = {
        "sender": {"user_id": "u_2"},
        "history": [{"message_id": "old_1"}],
        "business": {"business_id": "b_1"},
        "business_history": {"last_order_date": "2026-01-01"},
        "group": {"group_id": "g_1"},
        "group_membership": {"role": "admin"},
        "daily_notification_summary": {"count": 15}
    }
    features = extractor.extract(context, {})
    
    assert features["sender_trust"] == 0.8
    assert features["business_trust"] == 1.0
    assert features["group_priority"] == 1.0
    assert features["notification_load"] == 15

def test_quiet_hours(extractor):
    context = {
        "message": {
            "created_at": "2026-08-01 23:15"
        }
    }
    features = extractor.extract(context, {})
    assert features["quiet_hours"] is True

    context_day = {
        "message": {
            "created_at": "2026-08-01 12:15"
        }
    }
    features_day = extractor.extract(context_day, {})
    assert features_day["quiet_hours"] is False
