"""Stage persistence utilities.

This module provides helpers to persist the current UI stage (quota/dashboard)
across Streamlit refreshes.
"""

import os

CACHE_DIR = ".streamlit_cache"
STAGE_CACHE_FILE = os.path.join(CACHE_DIR, "stage.txt")


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    os.makedirs(CACHE_DIR, exist_ok=True)


def save_stage_cache(stage: str):
    """Persist the current stage (quota or dashboard) to cache."""
    ensure_cache_dir()
    try:
        with open(STAGE_CACHE_FILE, "w") as f:
            f.write(stage)
    except Exception:
        pass


def load_stage_cache() -> str:
    """Load the cached stage from disk, defaults to 'quota'."""
    if os.path.exists(STAGE_CACHE_FILE):
        try:
            with open(STAGE_CACHE_FILE, "r") as f:
                return f.read().strip() or "quota"
        except Exception:
            pass
    return "quota"
