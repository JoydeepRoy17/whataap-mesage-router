"""
Validator Module
Validates Gemini output against the Decision Contract.
"""
import json
import logging
import re
from typing import Optional, Dict, Any
from pydantic import ValidationError

from src.domain.decision_contract import AIResponse

logger = logging.getLogger(__name__)

class ResponseValidator:
    """
    Parses and validates the Gemini AI response.
    Repairs minor JSON formatting issues.
    """

    def validate(self, raw_response: str) -> Optional[AIResponse]:
        if not raw_response:
            logger.error("Empty response from AI.")
            return None

        cleaned_json = self._repair_json(raw_response)
        
        try:
            parsed = json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
            return None

        try:
            # Validate against Pydantic model
            ai_response = AIResponse(**parsed)
            return ai_response
        except ValidationError as e:
            logger.error(f"Validation error against AIResponse schema: {e}")
            return None

    def _repair_json(self, raw_str: str) -> str:
        """
        Attempts to strip markdown code blocks and fix minor formatting issues.
        """
        s = raw_str.strip()
        # Remove markdown code blocks if present
        if s.startswith("```json"):
            s = s[7:]
        elif s.startswith("```"):
            s = s[3:]
        if s.endswith("```"):
            s = s[:-3]
            
        s = s.strip()
        
        # Some LLMs return trailing commas which breaks standard json
        s = re.sub(r',\s*([\]}])', r'\1', s)
        
        return s
