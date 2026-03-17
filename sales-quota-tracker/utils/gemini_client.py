"""Gemini (Google Generative AI) API client helper.

This module provides a small wrapper around the google.genai SDK to generate
text completions. It uses the GEMINI_API_KEY environment variable (or
Streamlit secrets) for authentication.
"""

import os

import google.genai as genai


def get_gemini_api_key() -> str | None:
    """Return the Gemini API key.

    Priority:
    1) GEMINI_API_KEY environment variable
    2) `.env` file (gemini_api_key or GEMINI_API_KEY)
    3) Streamlit secrets (gemini_api_key)
    """
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key

    # Support .env files (common in local dev environments)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k.strip() in {"GEMINI_API_KEY", "gemini_api_key"}:
                        return v.strip().strip('"').strip("'")
        except Exception:
            pass

    try:
        import streamlit as st

        return st.secrets.get("gemini_api_key")
    except Exception:
        return None


def _extract_text_from_response(resp) -> str:
    """Extract text content from a Gemini GenerateContentResponse."""

    text_parts: list[str] = []

    # The response includes a candidates list; each candidate contains content.parts.
    candidates = getattr(resp, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        if not content:
            continue

        # Some Gemini responses use `content.parts`; others use `content.text`.
        parts = getattr(content, "parts", None)
        if parts:
            for part in parts:
                txt = getattr(part, "text", None)
                if txt:
                    text_parts.append(txt)

        if not text_parts:
            txt = getattr(content, "text", None)
            if txt:
                text_parts.append(txt)

    if text_parts:
        return "".join(text_parts)

    # Fallback: try stringifying.
    return str(resp)


_gemini_client: genai.Client | None = None


def _get_gemini_client(api_key: str) -> genai.Client:
    """Return a reusable Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def completion(prompt: str, model: str | None = None, max_tokens: int = 4096, stream: bool = False):
    """Generate a completion using the Gemini API.

    Args:
        prompt: The prompt text to send.
        model: Gemini model (e.g. gemini-1.5, gemini-2.0). Defaults to env `GEMINI_MODEL` or `models/gemini-2.5-flash`.
        max_tokens: Maximum number of output tokens.
        stream: If True, return a generator yielding text chunks.

    Returns:
        str (if stream=False) or generator of str chunks (if stream=True).

    Raises:
        RuntimeError: if the API key is missing or the request fails.
    """

    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError(
            "Gemini API key not found. Set the GEMINI_API_KEY environment variable or add it to Streamlit secrets (gemini_api_key)."
        )

    if model is None:
        # Use a current Gemini model that supports generateContent.
        # If you have access to a different model, set GEMINI_MODEL accordingly.
        model = os.environ.get("GEMINI_MODEL", "models/gemini-2.5-flash")

    client = _get_gemini_client(api_key)
    chat = client.chats.create(model=model)

    config = genai.types.GenerateContentConfig(maxOutputTokens=max_tokens, temperature=0.0)

    def _run():
        resp = chat.send_message(prompt, config=config)
        return _extract_text_from_response(resp)

    if stream:
        def _stream_generator():
            for resp in chat.send_message_stream(prompt, config=config):
                yield _extract_text_from_response(resp)

        return _stream_generator()

    try:
        return _run()
    except RuntimeError as e:
        # Retry once in case the underlying HTTP client was closed.
        if "client has been closed" in str(e).lower():
            # Reset client and retry.
            global _gemini_client
            _gemini_client = None
            client = _get_gemini_client(api_key)
            chat = client.chats.create(model=model)
            return _run()
        raise
