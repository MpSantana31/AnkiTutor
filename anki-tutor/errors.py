"""Error hierarchy for AnkiTutor (ADR-005 — Error Boundary).

All provider/runtime failures are mapped to a ``TutorError`` subclass so the
GUI can catch a single type and show a friendly, actionable message instead of
crashing the Anki hook.

Hierarchy (extends ADR-005 with ``ConfigError`` for local config issues):

    TutorError (base)
    ├── AuthError          # 401 — invalid/missing API key
    ├── RateLimitError     # 429 — provider throttling
    ├── RequestTimeoutError  # request timeout (avoids shadowing builtins.TimeoutError)
    ├── ProviderError      # 5xx / bad response / parse error
    └── ConfigError        # missing/invalid local config (no key, bad provider)
"""

from __future__ import annotations


class TutorError(Exception):
    """Base class for all AnkiTutor provider/runtime errors."""

    # Short, actionable hint shown to the user alongside the message.
    hint: str = ""

    @property
    def user_message(self) -> str:
        """Message plus optional hint, ready to display in the GUI."""
        if self.hint:
            return f"{self}\n\n{self.hint}"
        return str(self)


class AuthError(TutorError):
    """Authentication failed (HTTP 401) — invalid or missing API key."""

    hint = "Check your API key in Tools > AnkiTutor."


class RateLimitError(TutorError):
    """Provider rate limit hit (HTTP 429)."""

    hint = "Wait a moment or switch to another provider (OpenRouter/OpenCode)."


class RequestTimeoutError(TutorError):
    """Request to the provider timed out."""

    hint = "The provider took too long. Try again or pick a faster model."


class ProviderError(TutorError):
    """Generic provider failure (HTTP 5xx, bad response, parse error)."""

    hint = "The provider failed. Try another model or provider."


class ConfigError(TutorError):
    """Missing or invalid add-on configuration (e.g. no API key)."""

    hint = "Open Tools > AnkiTutor to configure the add-on."
