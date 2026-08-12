"""
Small, dumb wrapper around Groq's OpenAI-compatible chat endpoint.
No SDK dependency - just requests. Two functions:

  chat_json(...)  -> asks the model to return ONLY a JSON object and
                      parses it for you. Used for extraction/correction/
                      risk-assessment, where we need structured output.

  chat_text(...)  -> asks for a normal plain-text reply. Used for the
                      friendly chat message shown in the Copilot panel.

If you ever want to swap Groq for another OpenAI-compatible provider
(e.g. straight OpenAI, or a local vLLM server), this is the only file
you need to change.
"""
import json
import requests

from app.config import GROQ_API_KEY, GROQ_API_URL, EXTRACTION_MODEL


def _call_groq(messages: list[dict], model: str, json_mode: bool) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def chat_json(system_prompt: str, user_prompt: str, model: str = EXTRACTION_MODEL) -> dict:
    """Calls the model and parses its reply as JSON. Retries once
    (asking it to fix its own output) if parsing fails - LLMs
    occasionally wrap JSON in prose or code fences."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    raw = _call_groq(messages, model, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Give up gracefully rather than crashing the request.
            return {}


def chat_text(system_prompt: str, user_prompt: str, model: str = EXTRACTION_MODEL) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return _call_groq(messages, model, json_mode=False).strip()
