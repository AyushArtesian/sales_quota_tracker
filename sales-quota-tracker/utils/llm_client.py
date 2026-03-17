"""Abstract LLM client interface.

This module selects between available LLM backends (Groq, Gemini, etc.)
based on environment configuration.
"""

import os

# groq is optional; if not installed, Gemini becomes the default and Groq calls will fall back.
try:
    from .groq_client import completion as groq_completion
except Exception:
    groq_completion = None

from .gemini_client import completion as gemini_completion


def completion(prompt: str, model: str | None = None, max_tokens: int = 4096, stream: bool = False):
    """Dispatch to the configured LLM backend."""

    provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()

    if provider in {"gemini", "google", "google-gemini"}:
        return gemini_completion(prompt, model=model, max_tokens=max_tokens, stream=stream)

    # If Groq isn't installed or available, fall back to Gemini
    if groq_completion is None:
        return gemini_completion(prompt, model=model, max_tokens=max_tokens, stream=stream)

    return groq_completion(prompt, model=model, max_tokens=max_tokens, stream=stream)
