"""Helper utilities for AnkiTutor.

``extract_card`` pulls the front/back text out of an Anki card object so it can
be used as LLM context. Works with real ``anki.cards.Card`` (via the note) and
with the test ``FakeCard`` fixture.

.. function:: now()
              fmt_ts(iso_str)

   Centralised timestamp functions used by both ``tutor`` and ``gui`` (ADR-003).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

__all__ = [
    "SaveResult",
    "build_save_text",
    "extract_card",
    "extract_card_meta",
    "fmt_ts",
    "now",
    "save_answer_to_note",
]

try:
    from .prompts import DIRECT_MODES
except ImportError:  # imported directly (tests/CI without package context)
    from prompts import DIRECT_MODES


def now() -> str:
    """Return the current UTC time as an ISO-8601 string
    (e.g. ``2026-07-24T12:00:00Z``).

    Used by ``tutor._now``, ``gui._fmt_ts``, and other time-stamping needs.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_ts(iso_str: str) -> str:
    """Format an ISO-8601 timestamp like ``2026-07-24T12:00:00Z`` to ``24/07 12:00``.

    Returns the original string on parse failure.
    """
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(UTC).strftime("%d/%m %H:%M")
    except (ValueError, TypeError):
        return iso_str


def extract_card_meta(card: Any) -> tuple[int | None, int | None]:
    """Return ``(card_id, deck_id)`` for an Anki card or FakeCard.

    Used by the per-card history feature (ADR-008). Returns ``(None, None)``
    when the identifiers are unavailable (e.g. outside the Reviewer).
    """
    if card is None:
        return None, None

    # FakeCard used in tests: plain card_id/deck_id attributes (may be absent).
    card_id = getattr(card, "card_id", None)
    deck_id = getattr(card, "deck_id", None)
    if card_id is not None or deck_id is not None:
        return card_id, deck_id

    # Real Anki card: ``id``/``did`` are ints on anki.cards.Card.
    card_id = getattr(card, "id", None)
    deck_id = getattr(card, "did", None)
    if isinstance(card_id, int) or isinstance(deck_id, int):
        return (
            card_id if isinstance(card_id, int) else None,
            deck_id if isinstance(deck_id, int) else None,
        )

    return None, None


@dataclass
class SaveResult:
    """Outcome of :func:`save_answer_to_note` (message + field written)."""

    message: str
    field: str | None = None


def build_save_text(question: str, answer: str, mode: str = "explain") -> str:
    """Compose the text saved to the note: question + answer together.

    For direct modes (``simplify``/``example``/``relate``) the question is
    implicit, so the mode label is shown instead of a user-typed question.
    """
    if mode in DIRECT_MODES and not question.strip():
        q_label = f"[{mode}]"
    else:
        q_label = question.strip() or f"[{mode}]"
    return f"**Q:** {q_label}\n\n**A:** {answer.strip()}"


def save_answer_to_note(card: Any, text: str) -> SaveResult:
    """Append ``text`` to the card's note and persist it.

    Tries to find or auto-create a field named ``AnkiTutor`` on the note's
    model. If that's not possible (e.g. outside Anki or model not editable),
    returns an error message asking the user to add it manually.

    Works with both the real Anki ``Note`` (``note.fields`` is a list; accessed
    dict-like via ``note[name]``) and the test ``FakeCard``/``FakeNote``.

    Returns a :class:`SaveResult` (message + field written). Raises nothing.
    """
    note = getattr(card, "note", None)
    if callable(note):
        try:
            note = note()
        except (AttributeError, TypeError):
            return SaveResult("Could not access this card's note to save.")
    if note is None:
        return SaveResult("Could not access this card's note to save.")

    target = _resolve_target_field(note)

    # If "AnkiTutor" does not exist, try to create it automatically.
    if target != "AnkiTutor":
        if _ensure_anki_tutor_field(note):
            target = "AnkiTutor"
        else:
            return SaveResult(
                "No 'AnkiTutor' field found. Please add it to your note type: "
                "Edit the card (Ctrl+E) → Fields... → Add field → name it 'AnkiTutor'."
            )

    try:
        existing = (note[target] or "").strip()
    except (KeyError, TypeError, IndexError):
        return SaveResult("The 'AnkiTutor' field is not accessible on this note.")
    note[target] = f"{existing}\n\n{text}" if existing else text

    try:
        _persist_note(note)
    except (OSError, RuntimeError, AttributeError) as exc:
        return SaveResult(f"Could not save to note: {exc}")
    return SaveResult("Saved to note.", field=target)


def _get_field_names(note: Any) -> list[str]:
    """Extract field names from a note (Anki Note, FakeNote, or dict)."""
    names: list[str] = []
    keys = getattr(note, "keys", None)
    if callable(keys):
        try:
            names = list(keys())
        except (AttributeError, TypeError):
            names = []
    if not names:
        fields = getattr(note, "fields", None)
        if isinstance(fields, dict):
            names = list(fields.keys())
    return names


def _resolve_target_field(note: Any) -> str | None:
    """Return the field name to write to, or None when there are no fields.

    Prefers ``AnkiTutor``; otherwise the last field.
    """
    names = _get_field_names(note)
    if not names:
        return None
    return "AnkiTutor" if "AnkiTutor" in names else names[-1]


def _ensure_anki_tutor_field(note: Any) -> bool:
    """Try to create an 'AnkiTutor' field on the note's model (Anki only).

    Returns True if the field already exists or was successfully created.
    Returns False when outside Anki or the model cannot be edited.
    """
    mw = _get_mw()
    if mw is None:
        return False
    try:
        note_type = getattr(note, "note_type", None)
        if callable(note_type):
            note_type = note_type()
        if note_type is None:
            note_type = getattr(note, "model", None)
            if callable(note_type):
                note_type = note_type()
        if note_type is None:
            return False

        # Field already exists — nothing to do.
        for f in note_type["fields"]:
            if f["name"] == "AnkiTutor":
                return True

        new_field = mw.col.models.new_field("AnkiTutor")
        mw.col.models.add_field(note_type, new_field)
        mw.col.models.save(note_type)

        # Extend this note's fields list so it matches the updated model.
        note_fields = getattr(note, "fields", None)
        if isinstance(note_fields, list):
            note_fields.append("")

        return True
    except (KeyError, TypeError, AttributeError):
        return False


def _persist_note(note: Any) -> None:
    """Flush the note to the collection using the available Anki API.

    ``note.flush()`` only updates the in-memory object; we must also call the
    collection's ``update_note`` (modern API) and ``save`` so the change is
    committed to disk and survives closing Anki.
    """
    note.flush()
    mw = _get_mw()
    col = getattr(mw, "col", None) if mw is not None else None
    if col is not None:
        update = getattr(col, "update_note", None)
        if callable(update):
            update(note)
        col.save()


def _get_mw():
    """Best-effort import of Anki's main window; None outside Anki."""
    try:
        from aqt import mw

        return mw
    except ImportError:
        return None


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
        except (AttributeError, TypeError):
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
