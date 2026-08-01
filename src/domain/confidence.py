"""
Confidence Engine Module
Calculates a normalized final confidence score combining LLM confidence,
rule agreement, historical similarity, and trust/priority metrics.
"""
from typing import Dict, Any, List, Optional
from src.domain.decision_contract import AIResponse


class ConfidenceEngine:
    """
    Computes a weighted final confidence score normalized between 0.0 and 1.0.
    """

    def __init__(
        self,
        w_llm: float = 0.4,
        w_rule: float = 0.2,
        w_hist: float = 0.1,
        w_sender: float = 0.1,
        w_biz: float = 0.1,
        w_group: float = 0.1,
    ):
        self.w_llm = w_llm
        self.w_rule = w_rule
        self.w_hist = w_hist
        self.w_sender = w_sender
        self.w_biz = w_biz
        self.w_group = w_group

    def calculate(
        self,
        ai_response: Optional[AIResponse],
        rule_output: Dict[str, Any],
        features: Dict[str, Any],
        historical_messages: List[Dict[str, Any]],
    ) -> float:
        """
        Calculates the final normalized confidence score (0.0 to 1.0).
        """
        # 1. LLM Confidence score
        llm_conf = ai_response.confidence if ai_response else 0.5

        # 2. Rule Agreement (1.0 if AI action aligns with rule suggested action, else 0.0)
        rule_action = rule_output.get("suggested_action")
        ai_action = ai_response.action.value if ai_response else None
        
        # Mapping rules actions (allow/block/mute/notify) to AI ActionTypes (notify/digest/mute)
        rule_agreement = 0.5  # Neutral by default
        if ai_action and rule_action:
            if ai_action == rule_action:
                rule_agreement = 1.0
            elif (ai_action == "mute" and rule_action in ["mute", "block"]) or \
                 (ai_action == "notify" and rule_action in ["notify", "allow"]):
                rule_agreement = 0.8
            else:
                rule_agreement = 0.0

        # 3. Historical Similarity (Max relevance score normalized)
        max_hist_score = 0.0
        if historical_messages:
            max_score = max(msg.get("_relevance_score", 0.0) for msg in historical_messages)
            max_hist_score = min(max_score / 5.0, 1.0)

        # 4. Sender Trust
        sender_trust = float(features.get("sender_trust", 0.5))

        # 5. Business Trust
        business_trust = float(features.get("business_trust", 0.5))

        # 6. Group Priority
        group_priority = float(features.get("group_priority", 0.5))

        # Weighted Sum calculation
        weighted_score = (
            (llm_conf * self.w_llm) +
            (rule_agreement * self.w_rule) +
            (max_hist_score * self.w_hist) +
            (sender_trust * self.w_sender) +
            (business_trust * self.w_biz) +
            (group_priority * self.w_group)
        )

        total_weight = (
            self.w_llm + self.w_rule + self.w_hist +
            self.w_sender + self.w_biz + self.w_group
        )

        final_conf = weighted_score / total_weight if total_weight > 0 else 0.5
        return round(max(0.0, min(1.0, final_conf)), 4)
