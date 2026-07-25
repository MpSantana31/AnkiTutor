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


# --- Additional coverage tests for M4 ---


def test_map_error_429_raises_rate_limit(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    import requests
    from anki_tutor.errors import RateLimitError

    class _Resp:
        status_code = 429

        def raise_for_status(self):
            raise requests.HTTPError("429", response=self)

        def json(self):
            return {"error": {"message": "too many"}}

    def _boom(*a, **k):
        return _Resp()

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    with pytest.raises(RateLimitError):
        p.chat("ctx", "q?")


def test_map_error_generic_http_raises_provider_error(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    import requests
    from anki_tutor.errors import ProviderError

    class _Resp:
        status_code = 500

        def raise_for_status(self):
            raise requests.HTTPError("500", response=self)

        def json(self):
            return {"error": {"message": "internal"}}

    def _boom(*a, **k):
        return _Resp()

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    with pytest.raises(ProviderError):
        p.chat("ctx", "q?")


def test_error_detail_when_body_not_dict(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    import requests

    class _Resp:
        status_code = 401

        def raise_for_status(self):
            raise requests.HTTPError("401", response=self)

        def json(self):
            return ["not", "a", "dict"]

    def _boom(*a, **k):
        return _Resp()

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    from anki_tutor.errors import AuthError

    with pytest.raises(AuthError):
        p.chat("ctx", "q?")


def test_error_detail_attribute_error_on_response(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    import requests

    class _Resp:
        status_code = 500
        # No .json() method — triggers AttributeError in _error_detail

        def raise_for_status(self):
            raise requests.HTTPError("500", response=self)

    def _boom(*a, **k):
        return _Resp()

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    from anki_tutor.errors import ProviderError

    with pytest.raises(ProviderError):
        p.chat("ctx", "q?")


def test_error_detail_when_err_is_string(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    import requests

    class _Resp:
        status_code = 401

        def raise_for_status(self):
            raise requests.HTTPError("401", response=self)

        def json(self):
            return {"error": "bad key string"}

    def _boom(*a, **k):
        return _Resp()

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    from anki_tutor.errors import AuthError

    with pytest.raises(AuthError):
        p.chat("ctx", "q?")


def test_parse_response_not_a_dict():
    _load_addon()
    from anki_tutor.errors import ProviderError

    p = _make_provider()
    with pytest.raises(ProviderError):
        p._parse_response(["not a dict"])  # type: ignore[arg-type]


def test_parse_response_empty_content_without_length():
    _load_addon()
    from anki_tutor.errors import ProviderError

    p = _make_provider()
    with pytest.raises(ProviderError):
        p._parse_response(
            {"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]}
        )


def test_chat_no_requests_raises(monkeypatch):
    _load_addon()
    from anki_tutor.providers.base import requests as orig_req

    monkeypatch.setattr("anki_tutor.providers.base.requests", None)
    p = _make_provider()
    from anki_tutor.errors import ProviderError

    with pytest.raises(ProviderError):
        p.chat("ctx", "q?")
    monkeypatch.setattr("anki_tutor.providers.base.requests", orig_req)


def test_chat_value_error_handling(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    import requests

    def _boom(*a, **k):
        raise ValueError("bad parse")

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    from anki_tutor.errors import ProviderError

    with pytest.raises(ProviderError):
        p.chat("ctx", "q?")


def test_chat_request_exception_handling(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()
    import requests

    def _boom(*a, **k):
        raise requests.RequestException("connection error")

    monkeypatch.setattr(requests, "post", _boom)
    p = _make_provider()
    from anki_tutor.errors import ProviderError

    with pytest.raises(ProviderError):
        p.chat("ctx", "q?")


def test_chat_stream_no_api_key_without_callback():
    _load_addon()
    p = _make_provider(api_key="")
    from anki_tutor.errors import AuthError

    with pytest.raises(AuthError):
        p.chat_stream("ctx", "q?")


def test_chat_stream_no_api_key_with_callback():
    _load_addon()
    p = _make_provider(api_key="")
    errors = []
    result = p.chat_stream("ctx", "q?", "explain", on_error=errors.append)
    assert len(errors) == 1
    assert "No API key configured" in str(errors[0])
    assert result == ""


def test_chat_stream_no_requests_without_callback(monkeypatch):
    _load_addon()
    from anki_tutor.providers.base import requests as orig_req

    monkeypatch.setattr("anki_tutor.providers.base.requests", None)
    p = _make_provider()
    from anki_tutor.errors import ProviderError

    with pytest.raises(ProviderError):
        p.chat_stream("ctx", "q?")
    monkeypatch.setattr("anki_tutor.providers.base.requests", orig_req)


def test_chat_stream_no_requests_with_callback(monkeypatch):
    _load_addon()
    from anki_tutor.providers.base import requests as orig_req

    monkeypatch.setattr("anki_tutor.providers.base.requests", None)
    p = _make_provider()
    errors = []
    result = p.chat_stream("ctx", "q?", "explain", on_error=errors.append)
    monkeypatch.setattr("anki_tutor.providers.base.requests", orig_req)
    assert len(errors) == 1
    assert "requests is not available" in str(errors[0])
    assert result == ""


def test_chat_stream_without_on_token(monkeypatch):
    pytest.importorskip("requests")
    _load_addon()

    sse_lines = [
        'data: {"choices":[{"delta":{"content":"hello"}}]}',
        "data: [DONE]",
    ]

    class _Resp:
        def raise_for_status(self):
            pass

        def iter_lines(self, decode_unicode=True):
            return iter(sse_lines)

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp())
    p = _make_provider()
    full = p.chat_stream("ctx", "q?", "explain")
    assert full == "hello"


def test_llm_provider_chat_stream_fallback():
    """ABC fallback calls chat() and emits via callbacks."""
    _load_addon()
    from anki_tutor.providers.base import LLMProvider

    class Concrete(LLMProvider):
        name = "test"

        def chat(self, context, question, mode="explain"):
            return f"answer: {question}"

    p = Concrete()
    tokens = []
    done = []
    result = p.chat_stream(
        "ctx", "q?", "explain", on_token=tokens.append, on_done=done.append
    )
    assert tokens == ["answer: q?"]
    assert done == ["answer: q?"]
    assert result == "answer: q?"


def test_llm_provider_chat_stream_fallback_error():
    """ABC fallback routes chat() exceptions to on_error."""
    _load_addon()
    from anki_tutor.errors import ProviderError
    from anki_tutor.providers.base import LLMProvider

    class Broken(LLMProvider):
        name = "broken"

        def chat(self, context, question, mode="explain"):
            raise ProviderError("boom")

    p = Broken()
    errors = []
    result = p.chat_stream("ctx", "q?", "explain", on_error=errors.append)
    assert len(errors) == 1
    assert "boom" in str(errors[0])
    assert result == ""


def test_openrouter_extra_headers():
    _load_addon()
    from anki_tutor.providers.openrouter import OpenRouterProvider

    p = OpenRouterProvider(api_key="sk-x", model="gpt-4o", language="en")
    headers = p._extra_headers()
    assert headers["HTTP-Referer"] == "https://github.com/MpSantana31/AnkiTutor"
    assert headers["X-Title"] == "AnkiTutor"


def test_register_provider():
    _load_addon()
    from anki_tutor.providers.base import LLMProvider
    from anki_tutor.providers.factory import _PROVIDERS, register_provider

    class DummyProvider(LLMProvider):
        name = "dummy"

        def chat(self, context, question, mode="explain"):
            return "dummy"

    register_provider("dummy", DummyProvider)
    assert "dummy" in _PROVIDERS
    assert _PROVIDERS["dummy"] is DummyProvider
