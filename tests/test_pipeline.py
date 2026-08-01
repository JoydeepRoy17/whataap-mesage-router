import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd

from src.pipeline import MessageRouterPipeline

@pytest.fixture
def test_env(tmp_path):
    dataset_dir = tmp_path / "dataset"
    output_dir = tmp_path / "outputs"
    dataset_dir.mkdir()

    (dataset_dir / "messages.csv").write_text(
        "message_id,user_id,sender_user_id,group_id,business_id,conversation_type,created_at,message_text,media_type,media_id,forwarded_count\n"
        "msg_1,u_1,u_2,,,personal,2026-07-30 10:00,Hello friend,,0\n"
        "msg_2,u_1,u_3,g_1,,group,2026-07-30 11:00,You won a lottery!,,0\n"
        "msg_3,u_1,u_4,,,personal,2026-07-30 12:00,Bad payload text,,0\n"
    )

    (dataset_dir / "users.csv").write_text("user_id,name\nu_1,Alice\nu_2,Bob\nu_3,Scammer\nu_4,Eve\n")
    (dataset_dir / "groups.csv").write_text("group_id,group_name\ng_1,Test Group\n")
    (dataset_dir / "group_members.csv").write_text("group_id,user_id,role\ng_1,u_1,member\n")

    return str(dataset_dir), str(output_dir)

@patch("src.domain.gemini_client.GeminiClient.generate_content")
def test_full_pipeline_run(mock_gemini, test_env):
    dataset_dir, output_dir = test_env

    # Mock AI output for msg_1
    mock_gemini.return_value = '{"action": "notify", "message_type": "personal", "reason": "Friendly message", "confidence": 0.9, "evidence_message_ids": []}'

    pipeline = MessageRouterPipeline(
        data_dir=dataset_dir,
        output_dir=output_dir,
        use_ai=True
    )
    results = pipeline.run()

    assert len(results) == 3

    # msg_1 should be notified based on AI / default allow
    assert results[0]["message_id"] == "msg_1"
    assert results[0]["action"] == "notify"

    # msg_2 is a lottery scam, rule engine override should block it, which maps to mute
    assert results[1]["message_id"] == "msg_2"
    assert results[1]["action"] == "mute"

    # Verify output.csv exists
    out_csv = Path(output_dir) / "output.csv"
    assert out_csv.exists()

    df_out = pd.read_csv(out_csv)
    assert len(df_out) == 3
    assert "action" in df_out.columns

@patch("src.domain.gemini_client.GeminiClient.generate_content")
def test_pipeline_resilience_to_message_error(mock_gemini, test_env):
    dataset_dir, output_dir = test_env
    mock_gemini.return_value = None  # AI fails

    pipeline = MessageRouterPipeline(
        data_dir=dataset_dir,
        output_dir=output_dir,
        use_ai=True
    )

    # Force error on context building for msg_1, and return empty for msg_2/3
    with patch.object(pipeline.context_engine, "build_context", side_effect=[Exception("Fatal context error"), {}, {}]):
        results = pipeline.run()

    assert len(results) == 3
    # msg_1 has exception error fallback
    assert results[0]["message_id"] == "msg_1"
    assert "Pipeline processing exception" in results[0]["reason"]
    
    # msg_2 has missing context fallback
    assert results[1]["message_id"] == "msg_2"
    assert "Context could not be built" in results[1]["reason"]
