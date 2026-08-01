"""
Media Engine Module
Prepares message media metadata for downstream AI processing.
Does NOT perform OCR, transcription, or classification.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

from src.ingestion.loader import CSVLoader

logger = logging.getLogger(__name__)


class MediaEngine:
    """
    Resolves media references from a message into a standardised media object.

    Supported media types:
      - text  : plain text messages (no media attachment)
      - image : image messages looked up via images.csv
      - voice : voice-note messages looked up via voice_notes.csv

    The engine never opens, decodes, or classifies the actual media files.
    It only locates them and reports whether they exist on disk.
    """

    # Maps the media_type value in messages.csv to (csv filename, id column, path column)
    _MEDIA_REGISTRY: Dict[str, tuple] = {
        "image": ("images.csv", "media_id", "file_path"),
        "voice": ("voice_notes.csv", "media_id", "file_path"),
    }

    def __init__(self, loader: CSVLoader, media_root: str = "dataset") -> None:
        """
        Initialises the MediaEngine.

        Args:
            loader: A CSVLoader instance with datasets already cached.
            media_root: Root directory used to resolve relative file paths.
        """
        self.loader = loader
        self.media_root = Path(media_root)

    def prepare(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given a message dictionary, returns a standardised media object.

        Args:
            message: A single-row dictionary from messages.csv.

        Returns:
            A dictionary describing the media payload.
        """
        if not message:
            logger.warning("Empty message passed to MediaEngine.prepare().")
            return self._text_result("")

        media_type_raw = message.get("media_type")
        media_id = message.get("media_id")

        # ── Text messages (no media attachment) ──────────────────────────
        if pd.isna(media_type_raw) or media_type_raw is None or str(media_type_raw).strip() == "":
            text = message.get("message_text", "")
            if pd.isna(text):
                text = ""
            return self._text_result(str(text))

        media_type = str(media_type_raw).strip().lower()

        # ── Unknown / unsupported media type ─────────────────────────────
        if media_type not in self._MEDIA_REGISTRY:
            logger.warning(f"Unsupported media type '{media_type}' for message.")
            return self._text_result(message.get("message_text", ""))

        # ── Image or Voice ───────────────────────────────────────────────
        if pd.isna(media_id) or media_id is None or str(media_id).strip() == "":
            logger.warning(f"Message has media_type='{media_type}' but no media_id.")
            return self._media_result(media_type, media_id="", file_path="", exists=False)

        media_id = str(media_id).strip()
        csv_name, id_col, path_col = self._MEDIA_REGISTRY[media_type]

        file_path = self._lookup_file_path(csv_name, id_col, path_col, media_id)

        if file_path is None:
            logger.warning(f"media_id '{media_id}' not found in {csv_name}.")
            return self._media_result(media_type, media_id=media_id, file_path="", exists=False)

        full_path = self.media_root / file_path
        exists = full_path.exists()

        if not exists:
            logger.warning(f"Media file does not exist on disk: {full_path}")

        return self._media_result(
            media_type=media_type,
            media_id=media_id,
            file_path=str(file_path),
            exists=exists,
        )

    # ── Private helpers ──────────────────────────────────────────────────

    def _lookup_file_path(
        self, csv_name: str, id_col: str, path_col: str, media_id: str
    ) -> Optional[str]:
        """Looks up a file_path from a media-catalogue CSV by media_id."""
        df = self.loader.get_cached_dataset(csv_name)
        if df is None or df.empty:
            return None
        if id_col not in df.columns or path_col not in df.columns:
            logger.error(f"{csv_name} missing required columns '{id_col}' or '{path_col}'.")
            return None

        row = df[df[id_col] == media_id]
        if row.empty:
            return None

        value = row.iloc[0][path_col]
        if pd.isna(value):
            return None
        return str(value).strip()

    @staticmethod
    def _text_result(content: str) -> Dict[str, Any]:
        """Builds the standardised result dict for a text message."""
        return {
            "media_type": "text",
            "content": content,
        }

    @staticmethod
    def _media_result(
        media_type: str,
        media_id: str,
        file_path: str,
        exists: bool,
    ) -> Dict[str, Any]:
        """Builds the standardised result dict for an image/voice message."""
        return {
            "media_type": media_type,
            "media_id": media_id,
            "file_path": file_path,
            "exists": exists,
            "ready_for_ai": exists,
        }
