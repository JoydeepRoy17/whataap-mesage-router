"""
Historical Retrieval Module
Retrieves and ranks historical messages relevant to the current message.
"""
import logging
from typing import Dict, Any, List
import pandas as pd

from src.ingestion.loader import CSVLoader

logger = logging.getLogger(__name__)


class HistoricalRetriever:
    """
    Retrieves and ranks historical messages based on relevance criteria:
    - Same sender
    - Same business
    - Same group
    - Semantic similarity (Jaccard similarity on text)
    - Same category (conversation_type)
    - Same user interaction (presence in history or events)
    """

    def __init__(self, loader: CSVLoader):
        self.loader = loader

    def retrieve(self, current_message: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant historical messages for the same user.
        """
        if not current_message:
            return []

        user_id = current_message.get("user_id")
        current_msg_id = current_message.get("message_id")
        
        if not user_id or not current_msg_id:
            return []

        # Get all messages
        messages_df = self.loader.get_cached_dataset("messages.csv")
        if messages_df is None or messages_df.empty:
            return []

        # Filter messages for the same user, excluding the current message
        user_msgs = messages_df[(messages_df["user_id"] == user_id) & (messages_df["message_id"] != current_msg_id)]
        
        if user_msgs.empty:
            return []

        # Get interaction data
        history_df = self.loader.get_cached_dataset("message_history.csv")
        events_df = self.loader.get_cached_dataset("message_events.csv")
        
        interacted_msg_ids = set()
        if history_df is not None and not history_df.empty and "message_id" in history_df.columns:
            interacted_msg_ids.update(history_df[history_df["user_id"] == user_id]["message_id"].dropna().astype(str).tolist())
        if events_df is not None and not events_df.empty and "message_id" in events_df.columns:
            # Events apply to messages globally, just track if there's any event
            interacted_msg_ids.update(events_df["message_id"].dropna().astype(str).tolist())

        ranked_messages = []
        for _, row in user_msgs.iterrows():
            msg_dict = row.to_dict()
            score = self._calculate_relevance_score(current_message, msg_dict, interacted_msg_ids)
            msg_dict["_relevance_score"] = score
            ranked_messages.append(msg_dict)

        # Sort by score descending
        ranked_messages.sort(key=lambda x: x["_relevance_score"], reverse=True)
        
        # Clean NaNs and return top_k
        top_messages = ranked_messages[:top_k]
        return self._clean_nans(top_messages)

    def _calculate_relevance_score(self, current: Dict[str, Any], historical: Dict[str, Any], interacted_ids: set) -> float:
        score = 0.0

        # Same sender
        c_sender = current.get("sender_user_id")
        h_sender = historical.get("sender_user_id")
        if c_sender and h_sender and str(c_sender).strip() == str(h_sender).strip() and str(c_sender).strip() != "nan":
            score += 2.0

        # Same business
        c_biz = current.get("business_id")
        h_biz = historical.get("business_id")
        if c_biz and h_biz and str(c_biz).strip() == str(h_biz).strip() and str(c_biz).strip() != "nan":
            score += 2.0

        # Same group
        c_group = current.get("group_id")
        h_group = historical.get("group_id")
        if c_group and h_group and str(c_group).strip() == str(h_group).strip() and str(c_group).strip() != "nan":
            score += 2.0

        # Same category (conversation_type)
        c_type = current.get("conversation_type")
        h_type = historical.get("conversation_type")
        if c_type and h_type and str(c_type).strip() == str(h_type).strip() and str(c_type).strip() != "nan":
            score += 1.0

        # Semantic similarity (Jaccard)
        c_text = str(current.get("message_text", "")).lower()
        h_text = str(historical.get("message_text", "")).lower()
        if c_text != "nan" and h_text != "nan" and c_text and h_text:
            c_words = set(c_text.split())
            h_words = set(h_text.split())
            if c_words and h_words:
                intersection = c_words.intersection(h_words)
                union = c_words.union(h_words)
                jaccard = len(intersection) / len(union)
                score += (jaccard * 2.0)  # max 2 points

        # Same user interaction (if the historical message had any recorded interaction)
        h_msg_id = str(historical.get("message_id"))
        if h_msg_id in interacted_ids:
            score += 1.0

        return score

    def _clean_nans(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._clean_nans(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_nans(item) for item in data]
        else:
            return None if pd.isna(data) else data
