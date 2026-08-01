"""
Gemini Client Module
Interfaces with the Gemini API to fetch routing decisions.
"""
import os
import json
import time
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Client for interacting with the Gemini API.
    Handles authentication, retries, timeouts, and rate limits without crashing.
    """

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def generate_content(self, prompt_data: Union[str, Dict[str, Any]], max_retries: int = 3, timeout_sec: int = 10) -> Optional[str]:
        """
        Sends the prompt (and optional inline media) to Gemini and returns the raw text response.
        prompt_data can be a string or a dict: {"text": str, "inline_data": Optional[{"mime_type": str, "data": str}]}
        """
        if not self.api_key:
            logger.error("GEMINI_API_KEY environment variable is missing.")
            return None

        url = f"{self.base_url}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        if isinstance(prompt_data, str):
            prompt_data = {"text": prompt_data}
            
        parts = []
        if "text" in prompt_data:
            parts.append({"text": prompt_data["text"]})
        if "inline_data" in prompt_data:
            parts.append({
                "inlineData": {
                    "mimeType": prompt_data["inline_data"]["mime_type"],
                    "data": prompt_data["inline_data"]["data"]
                }
            })
            
        payload = {
            "contents": [{"parts": parts}]
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        for attempt in range(1, max_retries + 1):
            start_time = time.time()
            try:
                text_len = len(prompt_data.get("text", ""))
                has_media = "inline_data" in prompt_data
                logger.info(f"Gemini Request (Attempt {attempt}): Sending {text_len} chars. Media included: {has_media}")
                
                with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                    latency = time.time() - start_time
                    logger.info(f"Gemini Response: Status {response.status}, Latency {latency:.2f}s")
                    
                    if response.status == 200:
                        body = response.read().decode("utf-8")
                        resp_data = json.loads(body)
                        candidates = resp_data.get("candidates", [])
                        if not candidates:
                            logger.error("No candidates in Gemini response.")
                            return None
                            
                        content_parts = candidates[0].get("content", {}).get("parts", [])
                        if not content_parts:
                            logger.error("No text parts in Gemini response.")
                            return None
                            
                        result_text = content_parts[0].get("text", "")
                        return result_text

            except urllib.error.HTTPError as e:
                latency = time.time() - start_time
                if e.code == 429:
                    logger.warning("Rate limited by Gemini API.")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Gemini API Error {e.code}: {e.reason}")
                    time.sleep(1)
                    continue
            except urllib.error.URLError as e:
                # Includes timeout
                latency = time.time() - start_time
                logger.error(f"Gemini Request Error (timeout/network) after {latency:.2f}s: {e}")
                time.sleep(1)
                continue
            except Exception as e:
                logger.error(f"Unexpected error calling Gemini: {e}")
                time.sleep(1)

        logger.error("All Gemini API attempts failed. Returning None.")
        return None
