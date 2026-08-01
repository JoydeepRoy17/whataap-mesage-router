"""
Rule Engine Module
Builds deterministic routing rules based on extracted features and context.
"""
from typing import Dict, Any


class RuleEngine:
    """
    Evaluates context and features to determine deterministic routing actions.
    """

    def evaluate(self, features: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates rules in priority order. Returns the first matching rule's decision.
        Returns:
            {
                "suggested_action": "allow" | "notify" | "mute" | "block",
                "risk_score": float (0.0 to 1.0),
                "reason": str,
                "rule_name": str
            }
        """
        message = context.get("message", {})
        text = str(message.get("message_text", "")).lower()
        
        # 1. Urgent family messages
        is_family = features.get("contains_family", False)
        is_urgent = features.get("contains_emergency", False) or features.get("contains_deadline", False) or "urgent" in text
        if is_family and is_urgent:
            return self._build_result("notify", 0.1, "Urgent family message detected", "urgent_family")

        # 2. Admin announcements
        is_group = message.get("conversation_type") == "group"
        role = str(context.get("group_membership", {}).get("role", "")).lower()
        if is_group and role == "admin":
            return self._build_result("notify", 0.0, "Group admin announcement", "admin_announcement")

        # 3. Lottery Scams
        if features.get("contains_lottery", False) or "lottery" in text:
            return self._build_result("block", 0.9, "Lottery scam detected", "lottery_scam")

        # 4. Investment Scams
        investment_keywords = ["invest", "guaranteed return", "double your money", "roi", "high yield"]
        if any(kw in text for kw in investment_keywords):
            return self._build_result("block", 0.85, "Investment scam detected", "investment_scam")

        # 5. Crypto Scams
        crypto_keywords = ["crypto", "bitcoin", "btc", "eth", "ethereum", "wallet seed"]
        if any(kw in text for kw in crypto_keywords):
            return self._build_result("block", 0.9, "Crypto scam detected", "crypto_scam")

        # 6. Unknown Payment Requests
        is_payment = features.get("contains_payment", False)
        trust = features.get("sender_trust", 1.0)
        if is_payment and trust < 0.5:
            return self._build_result("block", 0.8, "Unknown payment request", "unknown_payment")

        # 7. OTP Requests
        if features.get("contains_otp", False) or "otp" in text or "verification code" in text:
            return self._build_result("notify", 0.2, "OTP request detected", "otp_request")

        # 8. Repeated Promotions
        is_promo = features.get("contains_promotion", False) or features.get("contains_spam_keywords", False)
        notif_load = features.get("notification_load", 0)
        fwd_score = features.get("forwarded_score", 0.0)
        if is_promo and (notif_load > 3 or fwd_score > 0.4):
            return self._build_result("mute", 0.6, "Repeated promotion or high-volume spam", "repeated_promotion")

        # 9. Muted Groups
        group = context.get("group", {})
        group_membership = context.get("group_membership", {})
        is_muted = group_membership.get("is_muted") is True or group.get("is_muted") is True
        # If quiet hours and it's a group, we can also consider it muted if role isn't admin
        if is_group and is_muted:
            return self._build_result("mute", 0.0, "Group is muted by user", "muted_group")
        
        # Default action
        return self._build_result("allow", 0.0, "No specific routing rule matched", "default_allow")

    def _build_result(self, action: str, risk: float, reason: str, rule: str) -> Dict[str, Any]:
        return {
            "suggested_action": action,
            "risk_score": float(risk),
            "reason": reason,
            "rule_name": rule
        }
