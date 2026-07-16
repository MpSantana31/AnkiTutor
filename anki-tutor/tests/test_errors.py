"""Tests for ``errors`` module hierarchy (offline)."""

from __future__ import annotations

from errors import (  # addon dir is on sys.path via conftest
    AuthError,
    ConfigError,
    ProviderError,
    RateLimitError,
    RequestTimeoutError,
    TutorError,
)


def test_hierarchy():
    assert issubclass(AuthError, TutorError)
    assert issubclass(RateLimitError, TutorError)
    assert issubclass(RequestTimeoutError, TutorError)
    assert issubclass(ProviderError, TutorError)
    assert issubclass(ConfigError, TutorError)
    assert isinstance(AuthError("x"), TutorError)


def test_user_message_includes_hint():
    err = RateLimitError("rate limited")
    msg = err.user_message
    assert "rate limited" in msg
    assert "another provider" in msg


def test_does_not_shadow_builtin_timeout():
    import builtins

    assert RequestTimeoutError is not builtins.TimeoutError
    assert isinstance(RequestTimeoutError("x"), TutorError)
