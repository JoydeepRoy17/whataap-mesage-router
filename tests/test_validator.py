import pytest
from src.domain.validator import ResponseValidator

@pytest.fixture
def validator():
    return ResponseValidator()

def test_valid_json(validator):
    raw = '{"action": "notify", "message_type": "personal", "reason": "Test", "confidence": 0.9, "evidence_message_ids": []}'
    result = validator.validate(raw)
    assert result is not None
    assert result.action == "notify"
    assert result.message_type == "personal"

def test_json_with_markdown(validator):
    raw = '```json\n{"action": "mute", "message_type": "spam", "reason": "Spam", "confidence": 0.99, "evidence_message_ids": []}\n```'
    result = validator.validate(raw)
    assert result is not None
    assert result.action == "mute"

def test_json_with_trailing_comma(validator):
    raw = '{"action": "digest", "message_type": "promotion", "reason": "Promo", "confidence": 0.5, "evidence_message_ids": [],}'
    result = validator.validate(raw)
    assert result is not None
    assert result.action == "digest"

def test_invalid_json(validator):
    raw = '{not valid json}'
    result = validator.validate(raw)
    assert result is None

def test_invalid_schema(validator):
    # Missing required fields
    raw = '{"action": "notify"}'
    result = validator.validate(raw)
    assert result is None

def test_invalid_confidence(validator):
    # Confidence out of bounds
    raw = '{"action": "notify", "message_type": "personal", "reason": "Test", "confidence": 1.5, "evidence_message_ids": []}'
    result = validator.validate(raw)
    assert result is None

def test_empty_response(validator):
    assert validator.validate("") is None
    assert validator.validate(None) is None
