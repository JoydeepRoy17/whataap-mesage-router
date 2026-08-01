"""
Prompt Builder Module
Assembles a structured prompt for the Gemini AI model from all upstream module outputs.
"""
import json
import logging
import base64
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.domain.decision_contract import AIResponse

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Builds a deterministic prompt for the Gemini API.
    """

    def build(
        self,
        context: Dict[str, Any],
        media: Dict[str, Any],
        features: Dict[str, Any],
        historical_messages: List[Dict[str, Any]],
        rule_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Assembles the full prompt as a single deterministic string.
        """
        sections: List[str] = []

        # 1. System role
        sections.append("System Role: You are a WhatsApp Message Routing AI.")
        
        # 2. AI objective
        sections.append("AI Objective: Determine the optimal routing action for the incoming message to avoid overwhelming the user while preserving critical information.")
        
        # 3. Decision rules
        sections.append(
            "Decision Rules:\n"
            "- Prioritize user safety (block scams, spam).\n"
            "- Respect user preferences (muted groups, quiet hours).\n"
            "- Preserve important messages (OTPs, urgent family, admin).\n"
            "- Use rule engine output as a strong baseline but override if evidence dictates otherwise."
        )

        # 4. Current message
        message = context.get("message", {})
        sections.append(self._section("Current Message", message))

        # 5. User profile
        user = context.get("user", {})
        sections.append(self._section("User Profile", user))

        # 6. Sender profile
        sender = context.get("sender", {})
        sections.append(self._section("Sender Profile", sender))

        # 7. Group profile
        group = context.get("group", {})
        group_membership = context.get("group_membership", {})
        group_combined = {**group, **{"membership": group_membership}} if group else {}
        sections.append(self._section("Group Profile", group_combined))

        # 8. Business profile
        business = context.get("business", {})
        business_history = context.get("business_history", {})
        business_combined = {**business, **{"history": business_history}} if business else {}
        sections.append(self._section("Business Profile", business_combined))

        # 9. Historical messages
        sections.append(self._section("Historical Messages", historical_messages))

        # 10. Extracted features
        sections.append(self._section("Extracted Features", features))

        # 11. Media summary
        sections.append(self._section("Media Summary", media))

        # 12. Rule Engine output
        sections.append(self._section("Rule Engine Output", rule_output))

        # 13. Expected JSON schema
        schema = AIResponse.model_json_schema()
        sections.append(self._section("Expected JSON schema", schema))

        # 14. Output instructions
        sections.append(
            "Output Instructions:\n"
            "Produce ONLY valid JSON matching the exact schema above.\n"
            "Do NOT output markdown formatting (like ```json).\n"
            "Do NOT output any explanations or conversational text outside the JSON."
        )

        prompt_text = "\n\n".join(sections)
        
        payload: Dict[str, Any] = {"text": prompt_text}

        # Handle multimodal attachment if media is valid and present on disk
        if media.get("is_valid") and media.get("absolute_path"):
            path_str = media.get("absolute_path")
            file_path = Path(path_str)
            if file_path.exists():
                try:
                    mime_type, _ = mimetypes.guess_type(path_str)
                    if not mime_type:
                        # Fallbacks
                        if media.get("type") == "image":
                            mime_type = "image/jpeg"
                        elif media.get("type") == "voice":
                            mime_type = "audio/ogg"
                        else:
                            mime_type = "application/octet-stream"

                    with open(file_path, "rb") as f:
                        data_bytes = f.read()
                    
                    b64_data = base64.b64encode(data_bytes).decode("utf-8")
                    
                    payload["inline_data"] = {
                        "mime_type": mime_type,
                        "data": b64_data
                    }
                except Exception as e:
                    logger.warning(f"Failed to read media file for multimodal prompt: {e}")

        return payload

    @staticmethod
    def _section(title: str, data: Any) -> str:
        try:
            body = json.dumps(data, indent=2, default=str)
        except (TypeError, ValueError):
            body = str(data)
        return f"{title}:\n{body}"
