"""
gemini_client.py

Wrapper for Google Gemini API calls.
Loads the API key from .env and provides helper functions
for structured LLM-based extraction and analysis.
"""

import os
import json
import time
import re
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

_client = None
_model = None


def _get_model():
    """Lazy-initialize the Gemini model."""
    global _client, _model
    if _model is not None:
        return _model

    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise RuntimeError(
            "GEMINI_API_KEY not set. "
            "Create a .env file in the project root with:\n"
            "GEMINI_API_KEY=your_key_here\n"
            "Get a free key at https://aistudio.google.com/apikey"
        )

    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel("gemini-2.0-flash")
    return _model


def call_gemini(prompt: str, max_retries: int = 3, expect_json: bool = True):
    """
    Send a prompt to Gemini and return the response.

    If expect_json=True, tries to parse the response as JSON.
    Falls back to raw text on parse failure.
    """
    model = _get_model()

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 8192,
                }
            )

            text = response.text.strip()

            if not expect_json:
                return text

            # Strip markdown code fences if present
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*\n?", "", text)
                text = re.sub(r"\n?```\s*$", "", text)

            return json.loads(text)

        except json.JSONDecodeError:
            # Try to extract JSON from the response
            json_match = re.search(r'[\[{].*[\]}]', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            if attempt == max_retries - 1:
                return {"raw_response": text, "parse_error": True}

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise RuntimeError(f"Gemini API error after {max_retries} attempts: {e}")

    return None


def is_api_available() -> bool:
    """Check if the Gemini API key is configured and valid."""
    try:
        _get_model()
        return True
    except Exception:
        return False
