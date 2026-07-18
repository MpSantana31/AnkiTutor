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

# Modes where the user does not type a question; the provider is asked to act on
# the whole card directly (see gui.py — input disabled for these modes).
DIRECT_MODES: tuple[str, ...] = ("simplify", "example", "relate")

# Implicit question sent to the provider for direct modes, per response language.
_IMPLICIT_QUESTIONS: dict[str, dict[str, str]] = {
    "explain": {"en": "Explain this card.", "pt-BR": "Explique este card."},
    "simplify": {
        "en": "Explain this card as if teaching a beginner.",
        "pt-BR": "Explique este card como se estivesse ensinando um iniciante.",
        "es": "Explica esta tarjeta como si enseñaras a un principiante.",
        "fr": "Expliquez cette carte comme à un débutant.",
        "de": "Erkläre diese Karte wie einem Anfänger.",
    },
    "example": {
        "en": "Explain this card and give a practical, concrete example.",
        "pt-BR": "Explique este card e dê um exemplo prático e concreto.",
        "es": "Explica esta tarjeta y da un ejemplo práctico y concreto.",
        "fr": "Expliquez cette carte et donnez un exemple pratique et concret.",
        "de": "Erkläre diese Karte und gib ein praktisches, konkretes Beispiel.",
    },
    "relate": {
        "en": "Explain this card and relate it to other common themes or concepts.",
        "pt-BR": "Explique este card e relacione-o a outros temas ou conceitos comuns.",
        "es": "Explica esta tarjeta y relaciónala con otros temas o conceptos comunes.",
        "fr": (
            "Expliquez cette carte et reliez-la à d'autres thèmes ou concepts courants."
        ),
        "de": "Erkläre diese Karte und setze sie mit anderen gängigen Themen in Bezug.",
    },
}


def implicit_question(mode: str, language: str = "en") -> str:
    """Return the fixed question used for direct modes (no user input).

    For non-direct modes (``explain``) returns the generic explain question.
    Falls back to English when the language is unsupported.
    """
    by_lang = _IMPLICIT_QUESTIONS.get(mode, _IMPLICIT_QUESTIONS["explain"])
    return by_lang.get(language, by_lang.get("en", "Explain this card."))


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
