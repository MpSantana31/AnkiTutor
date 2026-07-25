"""Per-card question history (ADR-008 — History Storage).

Persists past questions/answers as a JSON file in the add-on directory, keyed
by ``card_id``. The file contains user card content, so it is never committed
(see ``.gitignore``). All functions are tolerant of a missing/corrupt file.
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

try:
    from .tutor import TutorAnswer
except ImportError:  # imported directly (tests/CI without package context)
    from tutor import TutorAnswer

ADDON_DIR = Path(__file__).resolve().parent
HISTORY_PATH = ADDON_DIR / "history.json"


def _entry(answer: TutorAnswer) -> dict[str, Any]:
    return {
        "question": answer.question,
        "answer": answer.answer,
        "mode": answer.mode,
        "provider": answer.provider,
        "model": answer.model,
        "deck_id": answer.deck_id,
        "asked_at": answer.asked_at,
        "answered_at": answer.answered_at,
    }


def load_history(card_id: int | None) -> list[dict[str, Any]]:
    """Return the history list for ``card_id`` (empty if none/unavailable)."""
    if card_id is None:
        return []
    data = _read_all()
    return list(data.get(str(card_id), []))


def append_history(answer: TutorAnswer) -> None:
    """Append ``answer`` to the history of its ``card_id`` and persist it."""
    if answer.card_id is None:
        return
    data = _read_all()
    key = str(answer.card_id)
    data.setdefault(key, [])
    data[key].append(_entry(answer))
    _write_all(data)


def clear_history(card_id: int | None) -> None:
    """Remove all history entries for ``card_id`` and persist the change."""
    if card_id is None:
        return
    data = _read_all()
    key = str(card_id)
    data.pop(key, None)
    _write_all(data)


def _read_all() -> dict[str, Any]:
    if not HISTORY_PATH.exists():
        return {}
    try:
        text = HISTORY_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_all(data: dict[str, Any]) -> None:
    with contextlib.suppress(OSError):
        # Best-effort persistence: a failed write must not crash the panel.
        HISTORY_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
