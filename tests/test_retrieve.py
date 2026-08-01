import pytest
import pandas as pd
from pathlib import Path
from src.ingestion.loader import CSVLoader
from src.domain.retrieve import HistoricalRetriever

@pytest.fixture
def retriever_env(tmp_path):
    d = tmp_path / "dataset"
    d.mkdir()

    (d / "messages.csv").write_text(
        "message_id,user_id,sender_user_id,group_id,business_id,conversation_type,created_at,message_text\n"
        "msg_1,u_1,sender_1,,,personal,2026-07-30,Hello how are you\n"
        "msg_2,u_1,sender_1,,,personal,2026-07-29,Hello how are things\n" # high similarity, same sender
        "msg_3,u_1,sender_2,,,personal,2026-07-28,Completely different\n" # diff sender, diff text
        "msg_4,u_1,,,b_1,business,2026-07-27,Your invoice is ready\n" # biz
        "msg_5,u_1,,g_1,,group,2026-07-26,Group chat msg\n" # group
        "msg_6,u_2,sender_1,,,personal,2026-07-30,Different user\n"
    )

    (d / "message_history.csv").write_text(
        "message_id,user_id,status\n"
        "msg_2,u_1,read\n"
    )

    (d / "message_events.csv").write_text(
        "message_id,event_type\n"
        "msg_4,delivered\n"
    )

    loader = CSVLoader(data_dir=str(d))
    loader.load_all()
    return loader

def test_retrieve_personal_message(retriever_env):
    retriever = HistoricalRetriever(retriever_env)
    
    current_message = {
        "message_id": "msg_1",
        "user_id": "u_1",
        "sender_user_id": "sender_1",
        "conversation_type": "personal",
        "message_text": "Hello how are you doing"
    }

    results = retriever.retrieve(current_message, top_k=3)
    
    assert len(results) == 3
    # msg_2 should be ranked highest (same sender +2, same type +1, high similarity ~ +1, interacted +1 = ~5)
    assert results[0]["message_id"] == "msg_2"
    # others should follow
    assert "msg_6" not in [r["message_id"] for r in results] # Different user
    
def test_retrieve_business_message(retriever_env):
    retriever = HistoricalRetriever(retriever_env)
    
    current_message = {
        "message_id": "msg_new",
        "user_id": "u_1",
        "business_id": "b_1",
        "conversation_type": "business",
        "message_text": "New invoice"
    }

    results = retriever.retrieve(current_message, top_k=1)
    
    assert len(results) == 1
    # msg_4 should be highest due to business match
    assert results[0]["message_id"] == "msg_4"

def test_retrieve_group_message(retriever_env):
    retriever = HistoricalRetriever(retriever_env)
    
    current_message = {
        "message_id": "msg_new",
        "user_id": "u_1",
        "group_id": "g_1",
        "conversation_type": "group",
        "message_text": "hello"
    }

    results = retriever.retrieve(current_message, top_k=1)
    
    assert len(results) == 1
    # msg_5 should be highest due to group match
    assert results[0]["message_id"] == "msg_5"

def test_empty_message(retriever_env):
    retriever = HistoricalRetriever(retriever_env)
    assert retriever.retrieve({}) == []
