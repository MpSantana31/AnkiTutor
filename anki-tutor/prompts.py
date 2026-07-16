"""Prompt construction (ADR-002 — Context Injection Strategy).

The card front/back is injected as delimited text inside the system prompt.
Response "modes" are extra instructions appended to the same prompt.
"""

from __future__ import annotations

_MODE_INSTRUCTIONS: dict[str, str] = {
    "explain": "Explain the concept clearly and concisely.",
    "simplify": "Explain it as if teaching a beginner, using simple language.",
    "example": "Explain and then give a practical, concrete example.",
    "relate": "Explain and relate it to other common themes or concepts.",
}


def build_prompt(context: str, mode: str = "explain", language: str = "en") -> str:
    """Build the system prompt with card context and the chosen mode.

    ``context`` is the card's front+back text. ``mode`` selects an extra
    instruction. ``language`` is the desired response language code.
    """
    instruction = _MODE_INSTRUCTIONS.get(mode, _MODE_INSTRUCTIONS["explain"])
    return (
        "You are AnkiTutor, a study assistant that helps the user understand "
        "Anki flashcards. Always answer in the language with code "
        f"'{language}'.\n\n"
        "CARD CONTEXT:\n"
        f"{context}\n"
        "---\n"
        f"{instruction}\n"
        "Answer based ONLY on the CARD CONTEXT above. If the context is "
        "insufficient, say so briefly."
    )
