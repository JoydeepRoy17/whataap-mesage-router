import pytest
import pandas as pd
from pathlib import Path
from src.ingestion.loader import CSVLoader
from src.domain.media import MediaEngine


@pytest.fixture
def media_env(tmp_path):
    """
    Builds a minimal dataset directory with:
      - messages.csv
      - images.csv   (media catalogue)
      - voice_notes.csv (media catalogue)
      - an actual dummy image file on disk
      - an actual dummy voice file on disk
    Returns (loader, media_root_path)
    """
    d = tmp_path / "dataset"
    d.mkdir()

    # messages
    (d / "messages.csv").write_text(
        "message_id,user_id,conversation_type,created_at,message_text,media_type,media_id\n"
        "msg_1,u_1,personal,2026-07-30,Hello,,,\n"
        "msg_2,u_1,personal,2026-07-30,,image,img_001\n"
        "msg_3,u_1,personal,2026-07-30,,voice,vn_001\n"
        "msg_4,u_1,personal,2026-07-30,,image,img_999\n"
        "msg_5,u_1,personal,2026-07-30,,voice,\n"
        "msg_6,u_1,personal,2026-07-30,,video,vid_001\n"
    )

    # images catalogue
    (d / "images.csv").write_text(
        "image_id,file_path\n"
        "img_001,images/photo.jpg\n"
        "img_999,images/deleted.jpg\n"
    )

    # voice notes catalogue
    (d / "voice_notes.csv").write_text(
        "voice_note_id,file_path\n"
        "vn_001,voice/note.ogg\n"
    )

    # Create actual files for img_001 and vn_001, but NOT for img_999
    images_dir = d / "images"
    images_dir.mkdir()
    (images_dir / "photo.jpg").write_bytes(b"\xff\xd8fake-jpeg")

    voice_dir = d / "voice"
    voice_dir.mkdir()
    (voice_dir / "note.ogg").write_bytes(b"\x00fake-ogg")

    loader = CSVLoader(data_dir=str(d))
    loader.load_all()
    return loader, d


# ── Test: text message ───────────────────────────────────────────────────

def test_text_message(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare({
        "message_text": "Hello",
        "media_type": None,
        "media_id": None,
    })

    assert result == {"media_type": "text", "content": "Hello"}


def test_text_message_nan_media(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare({
        "message_text": "Hi there",
        "media_type": float("nan"),
        "media_id": float("nan"),
    })

    assert result == {"media_type": "text", "content": "Hi there"}


# ── Test: image message (file exists) ────────────────────────────────────

def test_image_exists(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare({
        "media_type": "image",
        "media_id": "img_001",
        "message_text": "",
    })

    assert result["media_type"] == "image"
    assert result["media_id"] == "img_001"
    assert result["file_path"] == "images/photo.jpg"
    assert result["exists"] is True
    assert result["ready_for_ai"] is True


# ── Test: image message (file missing on disk) ──────────────────────────

def test_image_file_missing(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare({
        "media_type": "image",
        "media_id": "img_999",
        "message_text": "",
    })

    assert result["media_type"] == "image"
    assert result["media_id"] == "img_999"
    assert result["exists"] is False
    assert result["ready_for_ai"] is False


# ── Test: voice message (file exists) ────────────────────────────────────

def test_voice_exists(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare({
        "media_type": "voice",
        "media_id": "vn_001",
        "message_text": "",
    })

    assert result["media_type"] == "voice"
    assert result["media_id"] == "vn_001"
    assert result["file_path"] == "voice/note.ogg"
    assert result["exists"] is True
    assert result["ready_for_ai"] is True


# ── Test: invalid media_id (not in catalogue CSV) ───────────────────────

def test_invalid_media_id(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare({
        "media_type": "image",
        "media_id": "img_DOES_NOT_EXIST",
        "message_text": "",
    })

    assert result["media_type"] == "image"
    assert result["media_id"] == "img_DOES_NOT_EXIST"
    assert result["file_path"] == ""
    assert result["exists"] is False
    assert result["ready_for_ai"] is False


# ── Test: empty media_id ─────────────────────────────────────────────────

def test_empty_media_id(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare({
        "media_type": "voice",
        "media_id": "",
        "message_text": "",
    })

    assert result["media_type"] == "voice"
    assert result["media_id"] == ""
    assert result["exists"] is False
    assert result["ready_for_ai"] is False


# ── Test: unsupported media type falls back to text ──────────────────────

def test_unsupported_media_type(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare({
        "media_type": "video",
        "media_id": "vid_001",
        "message_text": "Check this video",
    })

    assert result == {"media_type": "text", "content": "Check this video"}


# ── Test: empty message dict ─────────────────────────────────────────────

def test_empty_message(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare({})
    assert result == {"media_type": "text", "content": ""}


# ── Test: None message ───────────────────────────────────────────────────

def test_none_message(media_env):
    loader, root = media_env
    engine = MediaEngine(loader, media_root=str(root))

    result = engine.prepare(None)
    assert result == {"media_type": "text", "content": ""}
