"""Tests for provider base/factory (offline, no network)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

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


def test_chat_stream_emits_tokens(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()

    sse_lines = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        'data: {"choices":[{"delta":{"content":" world"}}]}',
        "data: [DONE]",
    ]

    class _Resp:
        def raise_for_status(self):
            pass

        def iter_lines(self, decode_unicode=True):
            return iter(sse_lines)

    def _ok(*a, **k):
        return _Resp()

    monkeypatch.setattr(requests, "post", _ok)
    p = _make_provider()
    tokens = []
    full = p.chat_stream("ctx", "q?", "explain", on_token=tokens.append)
    assert tokens == ["Hello", " world"]
    assert full == "Hello world"


def test_chat_stream_error_routes_to_callback(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    from anki_tutor.errors import AuthError as AE

    class _Resp:
        status_code = 401

        def raise_for_status(self):
            raise requests.HTTPError("401", response=self)

        def json(self):
            return {"error": {"message": "bad key"}}

        def iter_lines(self, decode_unicode=True):
            return iter([])

    def _boom(*a, **k):
        return _Resp()

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    errors = []
    p.chat_stream("ctx", "q?", "explain", on_error=errors.append)
    assert len(errors) == 1
    assert isinstance(errors[0], AE)


def test_chat_stream_skips_noise_and_empty_delta(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()

    sse_lines = [
        "",  # keep-alive blank line
        ": ping",  # comment line
        'data: {"choices":[{"delta":{}}]}',  # no content delta
        'data: {"choices":[{"delta":{"content":"X"}}]}',
        "data: [DONE]",
    ]

    class _Resp:
        def raise_for_status(self):
            pass

        def iter_lines(self, decode_unicode=True):
            return iter(sse_lines)

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp())
    p = _make_provider()
    tokens = []
    full = p.chat_stream("ctx", "q?", "explain", on_token=tokens.append)
    assert tokens == ["X"]
    assert full == "X"


def test_chat_stream_timeout_routes_to_callback(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    from anki_tutor.errors import RequestTimeoutError as TE

    def _boom(*a, **k):
        raise requests.Timeout("timeout")

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    errors = []
    p.chat_stream("ctx", "q?", "explain", on_error=errors.append)
    assert len(errors) == 1
    assert isinstance(errors[0], TE)


def test_chat_stream_fallback_when_no_requests(monkeypatch):
    _load_addon()
    import anki_tutor.providers.base as base

    monkeypatch.setattr(base, "requests", None)
    p = _make_provider()
    errors = []
    p.chat_stream("ctx", "q?", "explain", on_error=errors.append)
    assert len(errors) == 1
    assert "requests is not available" in str(errors[0])


def test_chat_stream_inline_error_in_sse(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    from anki_tutor.errors import ProviderError as PE

    sse_lines = ['data: {"error": {"message": "boom"}}']

    class _Resp:
        def raise_for_status(self):
            pass

        def iter_lines(self, decode_unicode=True):
            return iter(sse_lines)

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp())
    p = _make_provider()
    errors = []
    p.chat_stream("ctx", "q?", "explain", on_error=errors.append)
    assert len(errors) == 1
    assert isinstance(errors[0], PE)
    assert "boom" in str(errors[0])


def test_chat_stream_network_error_routes_to_callback(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    from anki_tutor.errors import ProviderError as PE

    def _boom(*a, **k):
        raise requests.RequestException("conn reset")

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    errors = []
    p.chat_stream("ctx", "q?", "explain", on_error=errors.append)
    assert len(errors) == 1
    assert isinstance(errors[0], PE)


def test_chat_stream_decodes_utf8_bytes_with_accents(monkeypatch):
    """Regression: accented chars must not become mojibake (você != vocÃª)."""
    pytest.importorskip("requests")
    _load_addon()

    # Raw SSE lines as bytes, exactly as a server would stream them over UTF-8.
    sse_bytes = [
        'data: {"choices":[{"delta":{"content":"você "}}]}'.encode(),
        'data: {"choices":[{"delta":{"content":"não"}}]}'.encode(),
        b"data: [DONE]",
    ]

    class _Resp:
        def raise_for_status(self):
            pass

        def iter_lines(self, decode_unicode=False):
            return iter(sse_bytes)

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp())
    p = _make_provider()
    tokens = []
    full = p.chat_stream("ctx", "q?", "explain", on_token=tokens.append)
    assert tokens == ["você ", "não"]
    assert full == "você não"
