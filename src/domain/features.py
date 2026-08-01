"""
Feature Extraction Module
Extracts structured features from the message context and media metadata.
"""
import re
from typing import Dict, Any

class FeatureExtractor:
    """
    Extracts structured features used by the Routing Engine.
    """

    def __init__(self):
        # Keyword lists for boolean features
        self.keywords = {
            "payment": ["pay", "payment", "rupees", "$", "transfer", "paid"],
            "invoice": ["invoice", "bill", "receipt"],
            "deadline": ["urgent", "today", "tomorrow", "asap", "deadline", "due"],
            "family": ["mom", "dad", "sister", "brother", "family", "wife", "husband"],
            "business": ["business", "corp", "ltd", "inc", "company"],
            "coupon": ["coupon", "discount", "offer", "promo code"],
            "otp": ["otp", "verification code", "one time password"],
            "lottery": ["lottery", "win", "prize", "winner", "jackpot"],
            "bank": ["bank", "account", "deposit", "withdrawal"],
            "event": ["event", "party", "wedding", "birthday", "celebration"],
            "meeting": ["meeting", "sync", "zoom", "meet", "schedule"],
            "school": ["school", "college", "university", "class", "homework", "exam"],
            "emergency": ["emergency", "help", "hospital", "police", "accident"],
            "promotion": ["promo", "sale", "discount", "free", "offer"],
            "spam_keywords": ["click here", "subscribe", "buy now", "free stuff", "act now"],
            "scam_keywords": ["urgent transfer", "password", "social security", "bank details", "lottery winner"]
        }

    def extract(self, context: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts features from context and media.
        """
        message = context.get("message", {})
        text = str(message.get("message_text", "")).lower()

        # If it's a text media type but we didn't use message_text
        if media.get("media_type") == "text" and media.get("content"):
            text = str(media.get("content")).lower()

        features = {}

        # 1. Keyword-based features
        for key, words in self.keywords.items():
            features[f"contains_{key}"] = any(word in text for word in words)

        # Special regex features
        features["contains_phone"] = bool(re.search(r'\b\d{10}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', text))
        features["contains_url"] = bool(re.search(r'http[s]?://|www\.', text))

        # 2. Forwarded score
        forwarded_count = message.get("forwarded_count", 0)
        try:
            forwarded_count = int(forwarded_count)
        except (ValueError, TypeError):
            forwarded_count = 0
        features["forwarded_score"] = float(min(forwarded_count / 5.0, 1.0)) # Normalize roughly

        # 3. Trust & Priority Scores
        features["sender_trust"] = self._calculate_sender_trust(context)
        features["business_trust"] = self._calculate_business_trust(context)
        features["group_priority"] = self._calculate_group_priority(context)

        # 4. Notification Load
        dns = context.get("daily_notification_summary", {})
        count = dns.get("count", 0)
        try:
            count = int(count)
        except (ValueError, TypeError):
            count = 0
        features["notification_load"] = count

        # 5. Quiet Hours
        created_at_str = message.get("created_at")
        features["quiet_hours"] = self._is_quiet_hours(created_at_str)

        return features

    def _calculate_sender_trust(self, context: Dict[str, Any]) -> float:
        """Calculates sender trust based on history."""
        history = context.get("history", [])
        sender = context.get("sender", {})
        if not sender:
            return 0.0
        # If user has history with messages, trust is higher
        if len(history) > 0:
            return 0.8
        return 0.5

    def _calculate_business_trust(self, context: Dict[str, Any]) -> float:
        """Calculates business trust based on business history."""
        biz = context.get("business", {})
        biz_hist = context.get("business_history", {})
        if not biz:
            return 0.0
        if biz_hist:
            return 1.0 # High trust if prior history
        return 0.5 # Neutral if no history but is a business

    def _calculate_group_priority(self, context: Dict[str, Any]) -> float:
        """Calculates group priority based on membership role."""
        group = context.get("group", {})
        membership = context.get("group_membership", {})
        if not group:
            return 0.0
        role = str(membership.get("role", "")).lower()
        if role == "admin":
            return 1.0
        elif role == "member":
            return 0.5
        return 0.2 # Unknown role

    def _is_quiet_hours(self, created_at_str: Any) -> bool:
        """Determines if the message was sent during quiet hours (e.g. 22:00 - 08:00)."""
        if not created_at_str or not isinstance(created_at_str, str):
            return False
        # Expected format: YYYY-MM-DD HH:MM
        try:
            time_part = created_at_str.split(" ")[1]
            hour = int(time_part.split(":")[0])
            if hour >= 22 or hour < 8:
                return True
        except (IndexError, ValueError):
            pass
        return False
