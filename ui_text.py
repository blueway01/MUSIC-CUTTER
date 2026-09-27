"""English and Japanese interface localization."""

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _japanese_messages() -> dict[str, str]:
    """Load the Japanese message catalog once."""
    catalog_path = Path(__file__).resolve().parent / "locales" / "ja.json"
    with catalog_path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def translate(message: str, language: str, **values: object) -> str:
    """Translate an English message and substitute named values."""
    template = _japanese_messages().get(message, message) if language == "Japanese" else message
    return template.format(**values) if values else template
