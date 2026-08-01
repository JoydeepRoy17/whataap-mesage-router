import pytest
from src.domain.prompt_builder import PromptBuilder

@pytest.fixture
def builder():
    return PromptBuilder()

def test_prompt_builder_structure(builder):
    context = {"message": {"message_text": "hello"}}
    payload = builder.build(context, {}, {}, [], {})
    
    assert isinstance(payload, dict)
    assert "text" in payload
    result = payload["text"]
    
    assert "System Role:" in result
    assert "AI Objective:" in result
    assert "Decision Rules:" in result
    assert "Current Message:" in result
    assert "User Profile:" in result
    assert "Sender Profile:" in result
    assert "Group Profile:" in result
    assert "Business Profile:" in result
    assert "Historical Messages:" in result
    assert "Extracted Features:" in result
    assert "Media Summary:" in result
    assert "Rule Engine Output:" in result
    assert "Expected JSON schema:" in result
    assert "Output Instructions:" in result

def test_prompt_builder_data_inclusion(builder):
    context = {"message": {"message_text": "secret123"}}
    features = {"contains_otp": True}
    rule_output = {"suggested_action": "notify"}
    
    payload = builder.build(context, {}, features, [], rule_output)
    
    assert isinstance(payload, dict)
    assert "text" in payload
    prompt = payload["text"]
    
    assert "secret123" in prompt
    assert "contains_otp" in prompt
    assert "notify" in prompt
