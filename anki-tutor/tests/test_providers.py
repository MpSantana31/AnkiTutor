"""Tests for provider base/factory (offline, no network)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_ADDON = Path(__file__).resolve().parent.parent


def _load_addon():
    if "anki_tutor" in sys.modules:
        return sys.modules["anki_tutor"]
    spec = importlib.util.spec_from_file_location("anki_tutor", _ADDON / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["anki_tutor"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_provider(api_key="sk-x", model="gpt-4o-mini"):
    _load_addon()
    from anki_tutor.providers.openai import OpenAIProvider

    return OpenAIProvider(api_key=api_key, model=model, language="en")


def test_no_api_key_raises():
    _load_addon()
    from anki_tutor.errors import AuthError

    p = _make_provider(api_key="")
    with pytest.raises(AuthError):
        p.chat("ctx", "q?")


def test_parse_response_happy_path():
    p = _make_provider()
    data = {"choices": [{"message": {"content": "  hello  "}}]}
    assert p._parse_response(data) == "hello"


def test_parse_response_error_field():
    _load_addon()
    from anki_tutor.errors import ProviderError

    p = _make_provider()
    with pytest.raises(ProviderError):
        p._parse_response({"error": {"message": "boom"}})


def test_parse_response_no_choices():
    _load_addon()
    from anki_tutor.errors import ProviderError

    p = _make_provider()
    with pytest.raises(ProviderError):
        p._parse_response({"choices": []})


def test_parse_response_truncated():
    _load_addon()
    from anki_tutor.errors import ProviderError

    p = _make_provider()
    with pytest.raises(ProviderError):
        p._parse_response(
            {"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}
        )


def test_extra_headers_hook_is_empty_by_default():
    _load_addon()
    p = _make_provider()
    assert p._extra_headers() == {}


def test_chat_network_timeout(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    import requests
    from anki_tutor.errors import RequestTimeoutError as TE

    def _boom(*a, **k):
        raise requests.Timeout("timeout")

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    with pytest.raises(TE):
        p.chat("ctx", "q?")


def test_chat_network_http_error_with_detail(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    import requests
    from anki_tutor.errors import AuthError as AE

    class _Resp:
        status_code = 401

        def raise_for_status(self):
            raise requests.HTTPError("401", response=self)

        def json(self):
            return {"error": {"message": "bad key"}}

    def _boom(*a, **k):
        return _Resp()

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    with pytest.raises(AE):
        p.chat("ctx", "q?")


def test_chat_network_success(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()

    import requests

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "answer text"}}]}

    def _ok(*a, **k):
        return _Resp()

    monkeypatch.setattr(requests, "post", _ok)
    p = _make_provider()
    assert p.chat("ctx", "question?") == "answer text"


def test_factory_requires_model():
    from anki_tutor.errors import ConfigError

    _load_addon()
    from anki_tutor.providers.factory import create_provider

    with pytest.raises(ConfigError):
        create_provider("openai", {"api_key": "x", "model": "", "language": "en"})


def test_factory_creates_openai_with_model():
    _load_addon()
    from anki_tutor.providers.factory import create_provider

    p = create_provider(
        "openai", {"api_key": "x", "model": "gpt-4o", "language": "pt-BR"}
    )
    assert p.name == "openai"
    assert p.model == "gpt-4o"
    assert p.language == "pt-BR"
