"""Minimal Groq (Qwen) API client helper.

This module enables making completion requests to the Groq API using the
qwen-72b model. It uses only the Python standard library and expects the
API key to be provided through an environment variable or Streamlit secrets.
"""

import os

from groq import Groq


def _load_dotenv(path: str) -> dict[str, str]:
    """Load a simple .env-style file into a dict.

    This supports lines like `KEY=value` and ignores comments.
    """
    result: dict[str, str] = {}
    if not os.path.exists(path):
        return result

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass

    return result


def get_groq_api_key() -> str | None:
    """Return the Groq API key.

    Priority:
    1) GROQ_API_KEY environment variable
    2) `.env` file (groq_api_key or GROQ_API_KEY)
    3) Streamlit secrets (groq_api_key)
    """
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key

    # Support .env files (common in local dev environments)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    dotenv = _load_dotenv(env_path)
    if "GROQ_API_KEY" in dotenv:
        return dotenv["GROQ_API_KEY"]
    if "groq_api_key" in dotenv:
        return dotenv["groq_api_key"]

    try:
        import streamlit as st

        return st.secrets.get("groq_api_key")
    except Exception:
        return None


def completion(prompt: str, model: str | None = None, max_tokens: int = 4096, stream: bool = False):
    """Generate a completion using the Groq SDK.

    Args:
        prompt: The prompt text to send.
        model: Groq model name (default from env or qwen/qwen3-32b).
        max_tokens: Maximum completion tokens.
        stream: If True, returns a generator yielding delta text chunks.

    Returns:
        str (if stream=False) or generator of str chunks (if stream=True).

    Raises:
        RuntimeError: if the API key is missing or the request fails.
    """

    api_key = get_groq_api_key()
    if not api_key:
        raise RuntimeError(
            "Groq API key not found. Set the GROQ_API_KEY environment variable or add it to Streamlit secrets (groq_api_key)."
        )

    if model is None:
        model = os.environ.get("GROQ_MODEL", "qwen/qwen3-32b")

    client = Groq(api_key=api_key)

    messages = [{"role": "user", "content": prompt}]

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        max_completion_tokens=max_tokens,
        top_p=0.95,
        reasoning_effort="default",
        stream=stream,
    )

    if stream:
        # Stream generator: yield partial text as it arrives
        for chunk in completion:
            try:
                delta = chunk.choices[0].delta
                if delta and hasattr(delta, "content"):
                    yield delta.content or ""
            except Exception:
                continue
        return

    # Non-streaming responses
    if hasattr(completion, "choices") and completion.choices:
        choice = completion.choices[0]
        if hasattr(choice, "message") and hasattr(choice.message, "content"):
            return choice.message.content
        if hasattr(choice, "text"):
            return choice.text

    return str(completion)
