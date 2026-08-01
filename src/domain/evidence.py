"""
Evidence Engine Module
Collects verifiable evidence supporting a routing decision.
Never fabricates IDs.
"""
from typing import Dict, Any, List, Optional
from src.domain.decision_contract import AIResponse


class EvidenceEngine:
    """
    Assembles evidence records supporting the routing decision.
    """

    def collect_evidence(
        self,
        ai_response: Optional[AIResponse],
        rule_output: Dict[str, Any],
        context: Dict[str, Any],
        historical_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Collects evidence items supporting the routing decision.

        Returns a list of evidence dictionaries, each containing:
            - type: "historical_message" | "rule_match" | "sender_match" | "business_match" | "group_match"
            - detail: str or dict describing the evidence
        """
        evidence: List[Dict[str, Any]] = []

        # 1. Historical Message IDs (Only validate against actually retrieved historical messages)
        valid_hist_ids = {str(msg.get("message_id")) for msg in historical_messages if msg.get("message_id")}
        
        if ai_response and ai_response.evidence_message_ids:
            for msg_id in ai_response.evidence_message_ids:
                if str(msg_id) in valid_hist_ids:
                    evidence.append({
                        "type": "historical_message",
                        "id": str(msg_id),
                        "detail": f"AI cited historical message {msg_id}"
                    })

        # 2. Matched Rule Name
        rule_name = rule_output.get("rule_name")
        if rule_name and rule_name != "default_allow":
            evidence.append({
                "type": "rule_match",
                "rule_name": rule_name,
                "reason": rule_output.get("reason", "")
            })

        # 3. Matching Sender
        sender = context.get("sender", {})
        if sender and sender.get("user_id"):
            evidence.append({
                "type": "sender_match",
                "sender_id": str(sender.get("user_id")),
                "sender_name": sender.get("name", "")
            })

        # 4. Matching Business
        business = context.get("business", {})
        if business and business.get("business_id"):
            evidence.append({
                "type": "business_match",
                "business_id": str(business.get("business_id")),
                "business_name": business.get("business_name", "")
            })

        # 5. Matching Group
        group = context.get("group", {})
        if group and group.get("group_id"):
            evidence.append({
                "type": "group_match",
                "group_id": str(group.get("group_id")),
                "group_name": group.get("group_name", "")
            })

        return evidence

    def extract_evidence_message_ids(
        self,
        ai_response: Optional[AIResponse],
        historical_messages: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Returns validated evidence message IDs (never fabricated).
        """
        valid_hist_ids = {str(msg.get("message_id")) for msg in historical_messages if msg.get("message_id")}
        if not ai_response or not ai_response.evidence_message_ids:
            return []
            
        validated_ids = [str(msg_id) for msg_id in ai_response.evidence_message_ids if str(msg_id) in valid_hist_ids]
        return validated_ids
