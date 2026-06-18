from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> None:
    app_root = Path(__file__).resolve().parents[3]
    load_dotenv(app_root / ".env")
    load_dotenv(app_root / "backend" / ".env")
