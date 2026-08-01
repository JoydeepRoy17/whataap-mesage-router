"""
Prompt Builder Module
Assembles a structured prompt for the Gemini AI model from all upstream
module outputs: context, media, features, historical messages, and rule engine.
"""
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# ── Expected JSON response schema (mirrors AIResponse in decision_contract.py) ──
EXPECTED_RESPONSE_SCHEMA: Dict[str, Any] = {
    "action": "notify | digest | mute",
    "message_type": (
        "personal | urgent | event | payment | business_update | "
        "promotion | greeting | forward | spam | scam | unknown"
    ),
    "reason": "<brief explanation for the decision>",
    "confidence": "<float between 0.0 and 1.0>",
    "evidence_message_ids": ["<list of historical message_ids supporting the decision>"],
}


class PromptBuilder:
    """
    Builds a two-part prompt (system + user) suitable for the Gemini API.

    The builder is stateless; every call to ``build`` produces an independent
    prompt pair from the supplied inputs.
    """

    # ── Public API ───────────────────────────────────────────────────────

    def build(
        self,
        context: Dict[str, Any],
        media: Dict[str, Any],
        features: Dict[str, Any],
        historical_messages: List[Dict[str, Any]],
        rule_output: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Assembles the full prompt.

        Args:
            context: Output of ``ContextEngine.build_context()``.
            media: Output of ``MediaEngine.prepare()``.
            features: Output of ``FeatureExtractor.extract()``.
            historical_messages: Output of ``HistoricalRetriever.retrieve()``.
            rule_output: Output of ``RuleEngine.evaluate()``.

        Returns:
            A dictionary with two keys:
                - ``system_prompt``: The system-role instruction string.
                - ``user_prompt``: The user-role data string.
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            context=context,
            media=media,
            features=features,
            historical_messages=historical_messages,
            rule_output=rule_output,
        )
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }

    # ── System Prompt ────────────────────────────────────────────────────

    @staticmethod
    def _build_system_prompt() -> str:
        """Returns the system-role instruction block."""
        return (
            "You are a WhatsApp Message Routing AI.\n\n"
            "## Role\n"
            "You are a senior notification-routing engine embedded in a WhatsApp "
            "client. Your sole job is to decide what should happen to an incoming "
            "message so the user receives the right level of attention without "
            "being overwhelmed.\n\n"
            "## Task\n"
            "Analyse the CURRENT MESSAGE together with the provided user context, "
            "group context, business context, historical messages, extracted "
            "features, media summary, and rule-engine output. Then return a "
            "single JSON object describing your routing decision.\n\n"
            "## Guidelines\n"
            "1. Prioritise user safety: block or flag scams and spam.\n"
            "2. Respect user preferences: honour muted groups and quiet hours.\n"
            "3. Preserve important messages: OTPs, urgent family, admin posts.\n"
            "4. Consider historical patterns when assessing trust and relevance.\n"
            "5. Use the rule-engine suggestion as a strong prior but override it "
            "if evidence warrants a different action.\n"
            "6. Your response MUST be valid JSON matching the schema provided.\n"
            "7. Do NOT include any text outside the JSON object.\n"
        )

    # ── User Prompt ──────────────────────────────────────────────────────

    def _build_user_prompt(
        self,
        context: Dict[str, Any],
        media: Dict[str, Any],
        features: Dict[str, Any],
        historical_messages: List[Dict[str, Any]],
        rule_output: Dict[str, Any],
    ) -> str:
        """Assembles all data sections into the user-role prompt string."""
        sections: List[str] = []

        # 1. Current Message
        message = context.get("message", {})
        sections.append(self._section("CURRENT MESSAGE", message))

        # 2. User Context
        user = context.get("user", {})
        sections.append(self._section("USER CONTEXT", user))

        # 3. Group Context
        group = context.get("group", {})
        group_membership = context.get("group_membership", {})
        group_combined = {**group, **{"membership": group_membership}} if group else {}
        sections.append(self._section("GROUP CONTEXT", group_combined))

        # 4. Business Context
        business = context.get("business", {})
        business_history = context.get("business_history", {})
        business_combined = {**business, **{"history": business_history}} if business else {}
        sections.append(self._section("BUSINESS CONTEXT", business_combined))

        # 5. Historical Messages
        sections.append(self._section("HISTORICAL MESSAGES", historical_messages))

        # 6. Extracted Features
        sections.append(self._section("EXTRACTED FEATURES", features))

        # 7. Media Summary
        sections.append(self._section("MEDIA SUMMARY", media))

        # 8. Rule Engine Output
        sections.append(self._section("RULE ENGINE OUTPUT", rule_output))

        # 9. Expected JSON Schema
        sections.append(self._section("EXPECTED JSON RESPONSE SCHEMA", EXPECTED_RESPONSE_SCHEMA))

        return "\n".join(sections)

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _section(title: str, data: Any) -> str:
        """Formats a titled section with pretty-printed JSON data."""
        try:
            body = json.dumps(data, indent=2, default=str)
        except (TypeError, ValueError):
            body = str(data)
        return f"## {title}\n```json\n{body}\n```\n"
