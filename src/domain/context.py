"""
Context Engine Module
Gathers all necessary data for making a notification routing decision.
"""
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
from src.ingestion.loader import CSVLoader

logger = logging.getLogger(__name__)

class ContextEngine:
    """
    Collects comprehensive context for a given message_id from cached DataFrames.
    Does not make routing decisions.
    """
    def __init__(self, loader: CSVLoader):
        """
        Initializes the ContextEngine with a configured CSVLoader instance.
        """
        self.loader = loader

    def _get_row_by_filters(self, df: Optional[pd.DataFrame], filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Helper to safely fetch a single row matching multiple column filters."""
        if df is None or df.empty:
            return None
            
        for col in filters.keys():
            if col not in df.columns:
                return None
                
        mask = pd.Series([True] * len(df), index=df.index)
        for col, val in filters.items():
            if pd.isna(val):
                return None
            mask &= (df[col] == val)
            
        row = df[mask]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def _get_row_as_dict(self, df: Optional[pd.DataFrame], filter_col: str, filter_val: Any) -> Optional[Dict[str, Any]]:
        """Helper to safely fetch a single row as a dictionary."""
        return self._get_row_by_filters(df, {filter_col: filter_val})

    def _get_rows_as_list(self, df: Optional[pd.DataFrame], filter_col: str, filter_val: Any) -> List[Dict[str, Any]]:
        """Helper to safely fetch multiple rows as a list of dictionaries."""
        if df is None or df.empty or filter_col not in df.columns:
            return []
        if pd.isna(filter_val):
            return []
            
        rows = df[df[filter_col] == filter_val]
        return rows.to_dict(orient="records")

    def _clean_nans(self, data: Any) -> Any:
        """Recursively replaces pandas NaNs with None for clean JSON serialization."""
        if isinstance(data, dict):
            return {k: self._clean_nans(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_nans(item) for item in data]
        else:
            return None if pd.isna(data) else data

    def build_context(self, message_id: str) -> Dict[str, Any]:
        """
        Builds a structured dictionary containing all required context for a message.
        """
        context = {
            "message": {},
            "user": {},
            "sender": {},
            "group": {},
            "group_membership": {},
            "business": {},
            "business_history": {},
            "history": [],
            "events": [],
            "daily_notification_summary": {}
        }

        # Message
        messages_df = self.loader.get_cached_dataset("messages.csv")
        message_dict = self._get_row_as_dict(messages_df, "message_id", message_id)
        if not message_dict:
            logger.warning(f"Message {message_id} not found in messages.csv.")
            return context
            
        context["message"] = message_dict
        
        user_id = message_dict.get("user_id")
        sender_id = message_dict.get("sender_user_id")
        group_id = message_dict.get("group_id")
        business_id = message_dict.get("business_id")
        
        # User
        users_df = self.loader.get_cached_dataset("users.csv")
        if user_id:
            context["user"] = self._get_row_as_dict(users_df, "user_id", user_id) or {}
            
        # Sender
        if sender_id:
            context["sender"] = self._get_row_as_dict(users_df, "user_id", sender_id) or {}

        # Group and Group Membership
        if group_id:
            groups_df = self.loader.get_cached_dataset("groups.csv")
            context["group"] = self._get_row_as_dict(groups_df, "group_id", group_id) or {}
            
            if user_id:
                group_members_df = self.loader.get_cached_dataset("group_members.csv")
                context["group_membership"] = self._get_row_by_filters(group_members_df, {"group_id": group_id, "user_id": user_id}) or {}

        # Business and Business History
        if business_id:
            biz_df = self.loader.get_cached_dataset("business_accounts.csv")
            context["business"] = self._get_row_as_dict(biz_df, "business_id", business_id) or {}
            
            if user_id:
                biz_hist_df = self.loader.get_cached_dataset("user_business_history.csv")
                context["business_history"] = self._get_row_by_filters(biz_hist_df, {"business_id": business_id, "user_id": user_id}) or {}

        # History and Events
        msg_hist_df = self.loader.get_cached_dataset("message_history.csv")
        if user_id:
            context["history"] = self._get_rows_as_list(msg_hist_df, "user_id", user_id)
            
        msg_events_df = self.loader.get_cached_dataset("message_events.csv")
        context["events"] = self._get_rows_as_list(msg_events_df, "message_id", message_id)

        # Daily notification summary
        dns_df = self.loader.get_cached_dataset("daily_notification_summary.csv")
        if user_id:
            context["daily_notification_summary"] = self._get_row_as_dict(dns_df, "user_id", user_id) or {}

        # Clean NaN values
        return self._clean_nans(context)
