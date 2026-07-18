"""Tests for ``providers.factory`` and ``tutor`` (offline, no network)."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

_ADDON = Path(__file__).resolve().parent.parent


def _load_addon():
    """Load the addon folder as package ``anki_tutor`` so relative imports work."""
    if "anki_tutor" in sys.modules:
        return sys.modules["anki_tutor"]
    spec = importlib.util.spec_from_file_location("anki_tutor", _ADDON / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["anki_tutor"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_factory_creates_openai():
    _load_addon()
    from anki_tutor.providers.factory import create_provider

    provider = create_provider(
        "openai",
        {
            "api_key": "sk-x",
            "model": "gpt-4o-mini",
            "language": "en",
            "api_keys": {"openai": "sk-x"},
        },
    )
    assert provider.name == "openai"
    assert provider.model == "gpt-4o-mini"


def test_factory_unknown_raises():
    _load_addon()
    from anki_tutor.errors import ConfigError
    from anki_tutor.providers.factory import create_provider

    with pytest.raises(ConfigError):
        create_provider("nope", {})


def test_tutor_ask_with_fake_provider(monkeypatch, fake_card):
    _load_addon()
    from anki_tutor import tutor
    from anki_tutor.tests.fixtures import FakeProvider

    monkeypatch.setattr(tutor, "create_provider", lambda name, cfg: FakeProvider())
    monkeypatch.setattr(
        tutor.config,
        "get_config",
        lambda: {
            "provider": "openai",
            "model": "m",
            "language": "en",
            "api_keys": {"openai": "x"},
        },
    )
    expected = (
        f"[fake] explain: what? | ctx=Front: {fake_card.front}\nBack: {fake_card.back}"
    )
    result = tutor.ask(fake_card, "what?")
    assert result.answer == expected
    assert result.question == "what?"
    assert result.mode == "explain"
    assert result.card_id == fake_card.card_id
    assert result.deck_id == fake_card.deck_id
    assert result.provider == "openai"
    assert result.model == "fake-model"
    assert result.timestamp


def test_tutor_ask_empty_question_raises(monkeypatch, fake_card):
    _load_addon()
    from anki_tutor import tutor
    from anki_tutor.errors import ConfigError

    monkeypatch.setattr(
        tutor.config,
        "get_config",
        lambda: {
            "provider": "openai",
            "model": "m",
            "language": "en",
            "api_keys": {"openai": "x"},
        },
    )
    with pytest.raises(ConfigError):
        tutor.ask(fake_card, "   ")


def test_tutor_ask_no_api_key_raises(monkeypatch, fake_card):
    _load_addon()
    from anki_tutor import tutor
    from anki_tutor.errors import ConfigError

    monkeypatch.setattr(
        tutor.config,
        "get_config",
        lambda: {
            "provider": "openai",
            "model": "m",
            "language": "en",
            "api_keys": {"openai": ""},
        },
    )
    with pytest.raises(ConfigError):
        tutor.ask(fake_card, "q?")


def _config_with_key():
    return {
        "provider": "openai",
        "model": "m",
        "language": "pt-BR",
        "api_keys": {"openai": "x"},
    }


def test_tutor_ask_stream_direct_mode_infers_question(monkeypatch, fake_card):
    _load_addon()
    from anki_tutor import tutor
    from anki_tutor.tests.fixtures import FakeProvider

    captured = {}

    def fake_create(name, cfg):
        captured["provider"] = name
        return FakeProvider()

    monkeypatch.setattr(tutor, "create_provider", fake_create)
    monkeypatch.setattr(tutor.config, "get_config", _config_with_key)

    tokens = []
    answer = tutor.ask_stream(fake_card, "", "simplify", on_token=tokens.append)
    assert "Explique este card" in answer
    assert tokens  # tokens were emitted via callback


def test_tutor_ask_explain_requires_question(monkeypatch, fake_card):
    _load_addon()
    from anki_tutor import tutor
    from anki_tutor.errors import ConfigError
    from anki_tutor.tests.fixtures import FakeProvider

    monkeypatch.setattr(tutor, "create_provider", lambda n, c: FakeProvider())
    monkeypatch.setattr(tutor.config, "get_config", _config_with_key)

    with pytest.raises(ConfigError):
        tutor.ask_stream(fake_card, "", "explain")
