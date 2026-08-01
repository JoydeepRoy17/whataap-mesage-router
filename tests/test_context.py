import pytest
import pandas as pd
from pathlib import Path
from src.ingestion.loader import CSVLoader
from src.domain.context import ContextEngine

@pytest.fixture
def mock_loader(tmp_path):
    d = tmp_path / "dataset"
    d.mkdir()
    
    (d / "messages.csv").write_text(
        "message_id,user_id,sender_user_id,group_id,business_id,conversation_type,created_at,message_text\n"
        "msg_1,u_1,u_2,,,personal,2026-07-30,Hello\n"
        "msg_2,u_1,u_3,g_1,,group,2026-07-30,Hi Group\n"
        "msg_3,u_1,,,b_1,business,2026-07-30,Order Update\n"
    )
    
    (d / "users.csv").write_text(
        "user_id,name,phone\n"
        "u_1,Alice,123\n"
        "u_2,Bob,456\n"
        "u_3,Charlie,789\n"
    )
    
    (d / "groups.csv").write_text(
        "group_id,group_name\n"
        "g_1,Family\n"
    )
    
    (d / "group_members.csv").write_text(
        "group_id,user_id,role\n"
        "g_1,u_1,admin\n"
    )
    
    (d / "business_accounts.csv").write_text(
        "business_id,business_name\n"
        "b_1,Amazon\n"
    )
    
    (d / "user_business_history.csv").write_text(
        "business_id,user_id,last_order_date\n"
        "b_1,u_1,2026-07-29\n"
    )
    
    (d / "message_history.csv").write_text(
        "message_id,user_id,status\n"
        "msg_old_1,u_1,read\n"
    )
    
    (d / "message_events.csv").write_text(
        "message_id,event_type\n"
        "msg_1,delivered\n"
    )
    
    (d / "daily_notification_summary.csv").write_text(
        "user_id,count\n"
        "u_1,5\n"
    )
    
    loader = CSVLoader(data_dir=str(d))
    loader.load_all()
    return loader

def test_personal_message(mock_loader):
    engine = ContextEngine(mock_loader)
    ctx = engine.build_context("msg_1")
    
    assert ctx["message"]["message_id"] == "msg_1"
    assert ctx["message"]["conversation_type"] == "personal"
    assert ctx["user"]["name"] == "Alice"
    assert ctx["sender"]["name"] == "Bob"
    
    # Should be empty dicts/lists since no group/business
    assert ctx["group"] == {}
    assert ctx["group_membership"] == {}
    assert ctx["business"] == {}
    assert ctx["business_history"] == {}
    
    # History and events
    assert len(ctx["history"]) == 1
    assert ctx["history"][0]["message_id"] == "msg_old_1"
    assert len(ctx["events"]) == 1
    assert ctx["events"][0]["event_type"] == "delivered"
    assert ctx["daily_notification_summary"]["count"] == 5

def test_group_message(mock_loader):
    engine = ContextEngine(mock_loader)
    ctx = engine.build_context("msg_2")
    
    assert ctx["message"]["message_id"] == "msg_2"
    assert ctx["group"]["group_name"] == "Family"
    assert ctx["group_membership"]["role"] == "admin"
    assert ctx["sender"]["name"] == "Charlie"
    
def test_business_message(mock_loader):
    engine = ContextEngine(mock_loader)
    ctx = engine.build_context("msg_3")
    
    assert ctx["message"]["message_id"] == "msg_3"
    assert ctx["business"]["business_name"] == "Amazon"
    assert ctx["business_history"]["last_order_date"] == "2026-07-29"
    assert ctx["sender"] == {}
    
def test_missing_groups_and_businesses(mock_loader):
    # Overwrite the groups with an empty file essentially
    d = Path(mock_loader.data_dir)
    (d / "groups.csv").write_text("group_id,group_name\n")
    mock_loader.clear_cache()
    mock_loader.load_all() # reload
    
    engine = ContextEngine(mock_loader)
    ctx = engine.build_context("msg_2")
    # Missing group gracefully handled
    assert ctx["group"] == {}
    # group_members still loaded but since group isn't there, wait, group_members is still there
    assert ctx["group_membership"]["role"] == "admin"

def test_missing_history(mock_loader):
    d = Path(mock_loader.data_dir)
    (d / "message_history.csv").unlink()
    # Need to clear cache to force exception handling or reload
    mock_loader.clear_cache()
    mock_loader.load_all()
    
    engine = ContextEngine(mock_loader)
    ctx = engine.build_context("msg_1")
    assert ctx["history"] == []
    
def test_invalid_message_id(mock_loader):
    engine = ContextEngine(mock_loader)
    ctx = engine.build_context("msg_invalid")
    assert ctx["message"] == {}
    assert ctx["user"] == {}
