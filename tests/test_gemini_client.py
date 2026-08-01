import pytest
import json
import urllib.error
from unittest.mock import patch, MagicMock
from src.domain.gemini_client import GeminiClient

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    return GeminiClient()

def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    c = GeminiClient()
    assert c.generate_content("test") is None

@patch("urllib.request.urlopen")
def test_successful_response(mock_urlopen, client):
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.status = 200
    
    mock_data = {
        "candidates": [{"content": {"parts": [{"text": "Hello Gemini"}]}}]
    }
    mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")
    mock_urlopen.return_value = mock_resp
    
    result = client.generate_content("prompt")
    assert result == "Hello Gemini"
    assert mock_urlopen.call_count == 1

@patch("urllib.request.urlopen")
def test_rate_limit_retry(mock_urlopen, client):
    # Setup HTTPError 429
    err = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
    
    mock_success = MagicMock()
    mock_success.__enter__.return_value = mock_success
    mock_success.status = 200
    mock_data = {
        "candidates": [{"content": {"parts": [{"text": "Success after retry"}]}}]
    }
    mock_success.read.return_value = json.dumps(mock_data).encode("utf-8")
    
    # First call throws 429, second returns 200
    mock_urlopen.side_effect = [err, mock_success]
    
    with patch("time.sleep") as mock_sleep:
        result = client.generate_content("prompt")
        
    assert result == "Success after retry"
    assert mock_urlopen.call_count == 2
    mock_sleep.assert_called_with(2) # 2**1 exponential backoff

@patch("urllib.request.urlopen")
def test_timeout_retry(mock_urlopen, client):
    err = urllib.error.URLError("timeout")
    mock_urlopen.side_effect = [err, err, err]
    
    with patch("time.sleep"):
        result = client.generate_content("prompt")
        
    assert result is None
    assert mock_urlopen.call_count == 3

@patch("urllib.request.urlopen")
def test_malformed_json_response(mock_urlopen, client):
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.status = 200
    # Missing candidates
    mock_resp.read.return_value = json.dumps({"candidates": []}).encode("utf-8")
    mock_urlopen.return_value = mock_resp
    
    result = client.generate_content("prompt")
    assert result is None

@patch("urllib.request.urlopen")
def test_multimodal_payload(mock_urlopen, client):
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}).encode("utf-8")
    mock_urlopen.return_value = mock_resp
    
    payload = {
        "text": "Analyze this image",
        "inline_data": {
            "mime_type": "image/jpeg",
            "data": "base64encodedstuff"
        }
    }
    client.generate_content(payload)
    
    # Verify the request payload contains inlineData
    req = mock_urlopen.call_args[0][0]
    sent_data = json.loads(req.data.decode("utf-8"))
    parts = sent_data["contents"][0]["parts"]
    assert len(parts) == 2
    assert "inlineData" in parts[1]
    assert parts[1]["inlineData"]["mimeType"] == "image/jpeg"
    assert parts[1]["inlineData"]["data"] == "base64encodedstuff"
