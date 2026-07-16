"""Tutor orchestrator (ADR-003 — blocking request).

Builds the card context, selects the configured provider via the factory, and
returns the model's answer. No streaming in the MVP.
"""

from __future__ import annotations

from . import config, utils
from .errors import ConfigError
from .providers import create_provider


def ask(card: object, question: str, mode: str = "explain") -> str:
    """Ask the configured provider about ``card`` using ``question``.

    Raises ``TutorError`` subclasses on any failure (ADR-005).
    """
    if not question or not question.strip():
        raise ConfigError("Please type a question.")

    cfg = config.get_config()
    provider_name = cfg.get("provider", "")
    api_keys = cfg.get("api_keys", {}) or {}
    if not api_keys.get(provider_name):
        raise ConfigError(
            f"No API key set for provider '{provider_name}'. "
            "Open Tools > AnkiTutor to configure."
        )

    front, back = utils.extract_card(card)
    context = f"Front: {front}\nBack: {back}"

    provider = create_provider(provider_name, cfg)
    return provider.chat(context, question.strip(), mode)
