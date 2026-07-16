"""Helper utilities for AnkiTutor.

``extract_card`` pulls the front/back text out of an Anki card object so it can
be used as LLM context. Works with real ``anki.cards.Card`` (via the note) and
with the test ``FakeCard`` fixture.
"""

from __future__ import annotations

from typing import Any


def extract_card(card: Any) -> tuple[str, str]:
    """Return ``(front, back)`` text for an Anki card or FakeCard.

    Falls back gracefully when fields are missing.
    """
    if card is None:
        return "", ""

    # FakeCard used in tests: plain front/back attributes.
    if hasattr(card, "front") and hasattr(card, "back"):
        return str(card.front), str(card.back)

    # Real Anki card: read from the note. ``card.note`` may be a method
    # (anki.cards.Card.note()) or a cached attribute, so call it if callable.
    note = getattr(card, "note", None)
    if callable(note):
        try:
            note = note()
        except Exception:  # noqa: BLE001
            note = None

    if note is not None:
        fields = getattr(note, "fields", None)
        if isinstance(fields, dict):
            values = list(fields.values())
            # Prefer explicit Front/Back names; fall back to field order.
            front = fields.get("Front") or (values[0] if values else "")
            back = fields.get("Back") or (values[1] if len(values) > 1 else "")
            return _strip_html(str(front)), _strip_html(str(back))

    # Last resort: rendered question/answer HTML.
    question = getattr(card, "question", "") or ""
    answer = getattr(card, "answer", "") or ""
    if callable(question):
        question = question()
    if callable(answer):
        answer = answer()
    return _strip_html(str(question)), _strip_html(str(answer))


def _strip_html(text: str) -> str:
    """Remove HTML tags, style/script blocks, and collapse whitespace."""
    import re

    text = re.sub(
        r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(
        r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", text).strip()
