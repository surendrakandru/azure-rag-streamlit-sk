import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Existing environment variables take precedence over .env.
load_dotenv(PROJECT_ROOT / ".env")


def required_setting(name: str) -> str:
    """Read a required setting without exposing its value."""
    value = os.getenv(name, "").strip()

    if not value:
        raise ValueError(f"Missing configuration setting: {name}")

    return value