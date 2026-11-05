"""Gemini JSON generation, using the same GENAI_API_KEY / gemini-2.5-flash setup as the rest of the backend."""
import json
import logging
import os
import re
import time

log = logging.getLogger("samvidhan.story.llm")

MODEL_NAME = os.environ.get("STORY_MODEL", "gemini-3.1-flash-lite")
TIMEOUT_S = 150
RETRIES = 2


class LLMError(Exception):
    pass


def _parse_json(text):
    text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.S)
    return json.loads(text)


def generate_json(system, prompt, temperature=0.7, images=None):
    """Call Gemini asking for JSON; retries transient failures. Never logs prompts (they contain source text)."""
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv
    except ImportError as e:  # pragma: no cover
        raise LLMError("google-generativeai is not installed") from e
    load_dotenv()
    key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise LLMError("No Gemini API key configured (GENAI_API_KEY).")
    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=system,
        generation_config={"response_mime_type": "application/json", "temperature": temperature},
    )
    last = None
    for attempt in range(RETRIES + 1):
        try:
            resp = model.generate_content([prompt, *images] if images else prompt, request_options={"timeout": TIMEOUT_S})
            return _parse_json(resp.text)
        except Exception as e:  # network, quota, safety block, bad JSON
            if type(e).__name__ in ("ResourceExhausted", "TooManyRequests"):
                # retrying a spent quota only burns more of it
                raise LLMError("The Gemini API quota for this key is used up. Wait a few minutes (per-minute limit) or until tomorrow (daily limit), or use a key with billing enabled.") from e
            last = e
            log.warning("gemini attempt %d failed: %s", attempt + 1, type(e).__name__)
            time.sleep(1.5 * (attempt + 1))
    raise LLMError(f"Generation failed after retries ({type(last).__name__}).")
