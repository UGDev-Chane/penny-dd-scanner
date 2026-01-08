from __future__ import annotations

from pathlib import Path

def load_env() -> None:
    """
    Load repo-root .env if present. Safe no-op if python-dotenv isn't installed
    or file doesn't exist.
    """
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    # repo root is two parents up from scanner/utils/env.py
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
