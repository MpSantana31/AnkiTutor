"""Provider factory (ADR-001 — Factory)."""

from __future__ import annotations

from ..errors import ConfigError
from .base import LLMProvider
from .openai import OpenAIProvider
from .opencode import OpenCodeGoProvider, OpenCodeZenProvider
from .openrouter import OpenRouterProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "openrouter": OpenRouterProvider,
    "opencode-zen": OpenCodeZenProvider,
    "opencode-go": OpenCodeGoProvider,
}


def register_provider(name: str, cls: type[LLMProvider]) -> None:
    """Register an additional provider (used by M3 add-ons)."""
    _PROVIDERS[name] = cls


def create_provider(name: str, config: dict) -> LLMProvider:
    """Build the provider instance for ``name`` using ``config``.

    Reads the provider-specific API key from ``config["api_keys"][name]`` so
    keys are kept separate per provider (never shared/mixed).
    """
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ConfigError(f"Unknown provider: {name}")

    model = config.get("model", "")
    if not model:
        raise ConfigError(f"No model selected for provider '{name}'.")

    api_keys = config.get("api_keys", {}) or {}
    api_key = api_keys.get(name, "")

    return cls(
        api_key=api_key,
        model=model,
        language=config.get("language", "en"),
    )
