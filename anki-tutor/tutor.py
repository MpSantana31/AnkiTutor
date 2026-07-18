"""Tutor orchestrator (ADR-003 — streaming request).

Builds the card context, selects the configured provider via the factory, and
returns a structured ``TutorAnswer``. ``ask`` is the blocking path (tests/CI);
``ask_stream`` is the user-facing streaming path (Observer callbacks).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC

from . import config, utils
from .errors import ConfigError
from .prompts import DIRECT_MODES, implicit_question
from .providers import create_provider


@dataclass
class TutorAnswer:
    """Structured answer returned by :func:`ask` (ADR-008).

    Carries enough metadata for the per-card history feature to persist and
    display past questions without re-querying the provider.
    """

    answer: str
    question: str
    mode: str
    card_id: int | None
    deck_id: int | None
    provider: str
    model: str
    timestamp: str


def ask(card: object, question: str, mode: str = "explain") -> TutorAnswer:
    """Ask the configured provider about ``card`` using ``question`` (blocking).

    Returns a :class:`TutorAnswer`. Raises ``TutorError`` subclasses on any
    failure (ADR-005). For direct modes (``simplify``/``example``/``relate``) the
    ``question`` may be omitted and is then inferred from the mode.
    """
    cfg = config.get_config()
    question = _resolve_question(question, mode, cfg)
    if not question.strip():
        raise ConfigError("Please type a question.")

    provider_name, provider, context, card_id, deck_id = _prepare(card, cfg)
    text = provider.chat(context, question.strip(), mode)

    return _pack(provider_name, provider, question, mode, card_id, deck_id, text)


def ask_stream(
    card: object,
    question: str,
    mode: str = "explain",
    on_token=None,
    on_done=None,
    on_error=None,
) -> str:
    """Stream the answer for ``card`` (ADR-003). Returns the full text.

    For direct modes the ``question`` is inferred from the mode when empty. The
    callbacks ``on_token``/``on_done``/``on_error`` receive stream events. On
    completion, the answer is persisted to the per-card history.
    """
    cfg = config.get_config()
    resolved = _resolve_question(question, mode, cfg)
    if not resolved.strip() and mode not in DIRECT_MODES:
        raise ConfigError("Please type a question.")

    provider_name, provider, context, card_id, deck_id = _prepare(card, cfg)
    text_holder = {"value": ""}

    fallback = (
        implicit_question(mode, cfg.get("language", "en"))
        if mode in DIRECT_MODES
        else ""
    )
    final_question = resolved.strip() or fallback

    def _on_done(full: str) -> None:
        text_holder["value"] = full
        answer = _pack(
            provider_name, provider, final_question, mode, card_id, deck_id, full
        )
        from .history import append_history

        append_history(answer)
        if on_done is not None:
            on_done(answer)

    return provider.chat_stream(
        context,
        final_question,
        mode,
        on_token=on_token,
        on_done=_on_done,
        on_error=on_error,
    )


def _resolve_question(question: str, mode: str, cfg: dict) -> str:
    """Infer the question for direct modes when the user typed nothing."""
    if (not question or not question.strip()) and mode in DIRECT_MODES:
        return implicit_question(mode, cfg.get("language", "en"))
    return question


def _prepare(card: object, cfg: dict):
    """Validate config/key and build provider + context (shared by ask/ask_stream)."""
    provider_name = cfg.get("provider", "")
    api_keys = cfg.get("api_keys", {}) or {}
    if not api_keys.get(provider_name):
        raise ConfigError(
            f"No API key set for provider '{provider_name}'. "
            "Open Tools > AnkiTutor to configure."
        )

    front, back = utils.extract_card(card)
    context = f"Front: {front}\nBack: {back}"
    card_id, deck_id = utils.extract_card_meta(card)
    provider = create_provider(provider_name, cfg)
    return provider_name, provider, context, card_id, deck_id


def _pack(
    provider_name, provider, question, mode, card_id, deck_id, text
) -> TutorAnswer:
    return TutorAnswer(
        answer=text,
        question=question.strip(),
        mode=mode,
        card_id=card_id,
        deck_id=deck_id,
        provider=provider_name,
        model=provider.model,
        timestamp=_now(),
    )


def _now() -> str:
    from datetime import datetime

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
