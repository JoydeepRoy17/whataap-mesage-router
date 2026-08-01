import pytest
import json
from src.domain.prompt_builder import PromptBuilder, EXPECTED_RESPONSE_SCHEMA


@pytest.fixture
def builder():
    return PromptBuilder()


@pytest.fixture
def sample_inputs():
    """A representative set of inputs from all upstream modules."""
    context = {
        "message": {
            "message_id": "msg_1",
            "user_id": "u_1",
            "sender_user_id": "u_2",
            "group_id": "g_1",
            "business_id": None,
            "conversation_type": "group",
            "created_at": "2026-07-30 10:00",
            "message_text": "Hello everyone",
        },
        "user": {"user_id": "u_1", "name": "Alice"},
        "sender": {"user_id": "u_2", "name": "Bob"},
        "group": {"group_id": "g_1", "group_name": "Family"},
        "group_membership": {"group_id": "g_1", "user_id": "u_1", "role": "admin"},
        "business": {},
        "business_history": {},
        "history": [{"message_id": "msg_old_1", "user_id": "u_1"}],
        "events": [{"message_id": "msg_1", "event_type": "delivered"}],
        "daily_notification_summary": {"user_id": "u_1", "count": 5},
    }
    media = {"media_type": "text", "content": "Hello everyone"}
    features = {
        "contains_payment": False,
        "contains_lottery": False,
        "contains_family": False,
        "contains_emergency": False,
        "forwarded_score": 0.0,
        "sender_trust": 0.8,
        "business_trust": 0.0,
        "group_priority": 1.0,
        "notification_load": 5,
        "quiet_hours": False,
    }
    historical_messages = [
        {"message_id": "msg_old_1", "message_text": "Previous message", "_relevance_score": 3.0}
    ]
    rule_output = {
        "suggested_action": "notify",
        "risk_score": 0.0,
        "reason": "Group admin announcement",
        "rule_name": "admin_announcement",
    }
    return context, media, features, historical_messages, rule_output


# ── Structure tests ──────────────────────────────────────────────────────


def test_build_returns_system_and_user_keys(builder, sample_inputs):
    result = builder.build(*sample_inputs)
    assert "system_prompt" in result
    assert "user_prompt" in result
    assert isinstance(result["system_prompt"], str)
    assert isinstance(result["user_prompt"], str)


def test_system_prompt_contains_role_and_task(builder, sample_inputs):
    result = builder.build(*sample_inputs)
    sp = result["system_prompt"]
    assert "WhatsApp Message Routing AI" in sp
    assert "## Role" in sp
    assert "## Task" in sp
    assert "## Guidelines" in sp
    assert "valid JSON" in sp


# ── User prompt section tests ────────────────────────────────────────────


def test_user_prompt_contains_all_sections(builder, sample_inputs):
    result = builder.build(*sample_inputs)
    up = result["user_prompt"]
    required_sections = [
        "CURRENT MESSAGE",
        "USER CONTEXT",
        "GROUP CONTEXT",
        "BUSINESS CONTEXT",
        "HISTORICAL MESSAGES",
        "EXTRACTED FEATURES",
        "MEDIA SUMMARY",
        "RULE ENGINE OUTPUT",
        "EXPECTED JSON RESPONSE SCHEMA",
    ]
    for section in required_sections:
        assert f"## {section}" in up, f"Missing section: {section}"


def test_user_prompt_contains_message_data(builder, sample_inputs):
    result = builder.build(*sample_inputs)
    up = result["user_prompt"]
    assert "msg_1" in up
    assert "Hello everyone" in up


def test_user_prompt_contains_group_context(builder, sample_inputs):
    result = builder.build(*sample_inputs)
    up = result["user_prompt"]
    assert "Family" in up
    assert "admin" in up


def test_user_prompt_contains_features(builder, sample_inputs):
    result = builder.build(*sample_inputs)
    up = result["user_prompt"]
    assert "contains_payment" in up
    assert "sender_trust" in up


def test_user_prompt_contains_rule_output(builder, sample_inputs):
    result = builder.build(*sample_inputs)
    up = result["user_prompt"]
    assert "admin_announcement" in up
    assert "Group admin announcement" in up


def test_user_prompt_contains_schema(builder, sample_inputs):
    result = builder.build(*sample_inputs)
    up = result["user_prompt"]
    assert "action" in up
    assert "message_type" in up
    assert "confidence" in up
    assert "evidence_message_ids" in up


# ── Edge case tests ──────────────────────────────────────────────────────


def test_empty_context(builder):
    result = builder.build(
        context={},
        media={},
        features={},
        historical_messages=[],
        rule_output={},
    )
    assert "system_prompt" in result
    assert "user_prompt" in result
    # All sections still present even with empty data
    up = result["user_prompt"]
    assert "CURRENT MESSAGE" in up
    assert "HISTORICAL MESSAGES" in up


def test_business_context_populated(builder):
    context = {
        "message": {"message_id": "msg_b1", "conversation_type": "business"},
        "user": {"user_id": "u_1"},
        "sender": {},
        "group": {},
        "group_membership": {},
        "business": {"business_id": "b_1", "business_name": "Amazon"},
        "business_history": {"last_order_date": "2026-07-29"},
        "history": [],
        "events": [],
        "daily_notification_summary": {},
    }
    result = builder.build(
        context=context,
        media={"media_type": "text", "content": ""},
        features={"business_trust": 1.0},
        historical_messages=[],
        rule_output={"suggested_action": "allow", "risk_score": 0.0, "reason": "ok", "rule_name": "default"},
    )
    up = result["user_prompt"]
    assert "Amazon" in up
    assert "last_order_date" in up


def test_expected_schema_constant_has_required_keys():
    assert "action" in EXPECTED_RESPONSE_SCHEMA
    assert "message_type" in EXPECTED_RESPONSE_SCHEMA
    assert "reason" in EXPECTED_RESPONSE_SCHEMA
    assert "confidence" in EXPECTED_RESPONSE_SCHEMA
    assert "evidence_message_ids" in EXPECTED_RESPONSE_SCHEMA
