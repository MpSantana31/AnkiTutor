"""LLM provider abstraction (ADR-001 — Strategy + Template Method).

``LLMProvider`` is the strategy interface; ``BaseHTTPProvider`` implements the
shared HTTP logic (headers, payload, error mapping). Concrete providers only
override ``base_url`` and, when needed, ``_extra_headers``.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

try:
    import requests
except ImportError:  # tests/CI may run without requests installed
    requests = None  # type: ignore[assignment]

from .. import prompts
from ..errors import (
    AuthError,
    ProviderError,
    RateLimitError,
    RequestTimeoutError,
    TutorError,
)


class LLMProvider(ABC):
    """Strategy interface for an LLM backend."""

    name: str = "base"

    @abstractmethod
    def chat(self, context: str, question: str, mode: str = "explain") -> str:
        """Return the model's answer given the card context and a question."""

    def chat_stream(
        self,
        context: str,
        question: str,
        mode: str = "explain",
        on_token: Any = None,
        on_done: Any = None,
        on_error: Any = None,
    ) -> str:
        """Stream the answer, emitting tokens via callbacks.

        Default implementation falls back to ``chat`` (useful for providers/tests
        without native streaming). Concrete HTTP providers override this with
        real SSE streaming (ADR-003).
        """
        try:
            answer = self.chat(context, question, mode)
        except TutorError as exc:
            if on_error is not None:
                on_error(exc)
            return ""
        if on_token is not None:
            on_token(answer)
        if on_done is not None:
            on_done(answer)
        return answer


class BaseHTTPProvider(LLMProvider):
    """Template Method: shared POST /chat/completions logic."""

    base_url: str = ""
    auth_scheme: str = "Bearer"

    def __init__(self, api_key: str, model: str, language: str = "en") -> None:
        self.api_key = api_key
        self.model = model
        self.language = language

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"{self.auth_scheme} {self.api_key}",
            "Content-Type": "application/json",
        }
        headers.update(self._extra_headers())
        return headers

    def _extra_headers(self) -> dict[str, str]:
        """Hook for provider-specific headers (overridden in M3 providers)."""
        return {}

    def _payload(self, context: str, question: str, mode: str) -> dict:
        system = prompts.build_prompt(context, mode, self.language)
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            "temperature": 0.3,
        }

    def _map_error(self, exc: Any) -> None:
        code = exc.response.status_code if exc.response is not None else 0
        detail = self._error_detail(exc.response)
        if code == 401:
            raise AuthError(f"Invalid or missing API key (401). {detail}") from exc
        if code == 429:
            raise RateLimitError(
                f"Rate limit reached (429). Try again later. {detail}"
            ) from exc
        raise ProviderError(f"Provider returned HTTP {code}. {detail}") from exc

    @staticmethod
    def _error_detail(response) -> str:
        try:
            body = response.json()
        except (ValueError, AttributeError):
            return ""
        err = body.get("error") if isinstance(body, dict) else None
        if isinstance(err, dict):
            return err.get("message", "")
        if isinstance(err, str):
            return err
        return ""

    def chat(self, context: str, question: str, mode: str = "explain") -> str:
        if not self.api_key:
            raise AuthError("No API key configured.")
        if requests is None:
            raise ProviderError("requests is not available in this environment.")

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=self._payload(context, question, mode),
                timeout=30,
            )
            resp.raise_for_status()
            return self._parse_response(resp.json())
        except requests.Timeout:
            raise RequestTimeoutError("Request to the provider timed out.") from None
        except requests.HTTPError as exc:
            self._map_error(exc)
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Unexpected provider response: {exc}") from exc
        except requests.RequestException as exc:
            raise ProviderError(f"Network error: {exc}") from exc

    def _parse_response(self, data: dict) -> str:
        """Extract the answer text from achat/completions response."""
        if not isinstance(data, dict):
            raise ProviderError("Provider response was not a JSON object.")
        if "error" in data:
            err = data["error"]
            msg = err.get("message", "") if isinstance(err, dict) else str(err)
            raise ProviderError(f"Provider error: {msg}")

        choices = data.get("choices")
        if not choices:
            raise ProviderError("Provider returned no choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not content:
            finish = choices[0].get("finish_reason")
            if finish == "length":
                raise ProviderError("Response truncated: model max tokens reached.")
            raise ProviderError("Provider returned an empty answer.")

        return content.strip()

    def chat_stream(
        self,
        context: str,
        question: str,
        mode: str = "explain",
        on_token: Any = None,
        on_done: Any = None,
        on_error: Any = None,
    ) -> str:
        """Stream tokens from the OpenAI-compatible ``/chat/completions`` SSE API.

        Emits each delta via ``on_token`` and the full text via ``on_done``.
        Errors are routed to ``on_error`` (or raised if no callback). Mapping of
        HTTP errors to ``TutorError`` mirrors :meth:`chat` (ADR-005).
        """
        if not self.api_key:
            exc = AuthError("No API key configured.")
            if on_error is not None:
                on_error(exc)
            else:
                raise exc
            return ""

        if requests is None:
            exc = ProviderError("requests is not available in this environment.")
            if on_error is not None:
                on_error(exc)
            else:
                raise exc
            return ""

        payload = self._payload(context, question, mode)
        payload["stream"] = True

        chunks: list[str] = []
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=30,
                stream=True,
            )
            resp.raise_for_status()
            # Decode as UTF-8 explicitly (not requests' guessed encoding, which
            # may fall back to Latin-1 for text/event-stream without charset and
            # mangle accented characters). Lines arrive as bytes via iter_lines.
            for raw in resp.iter_lines(decode_unicode=False):
                if not raw:
                    continue
                try:
                    if isinstance(raw, bytes):
                        line = raw.decode("utf-8", errors="replace")
                    else:
                        line = str(raw)
                except (UnicodeDecodeError, TypeError):
                    continue
                if line.startswith("data:"):
                    data_str = line[len("data:") :].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                    except (ValueError, TypeError):
                        continue
                    if "error" in data:
                        err = data["error"]
                        if isinstance(err, dict):
                            msg = err.get("message", "")
                        else:
                            msg = str(err)
                        raise ProviderError(f"Provider error: {msg}") from None
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    piece = delta.get("content")
                    if piece:
                        chunks.append(piece)
                        if on_token is not None:
                            on_token(piece)
        except requests.Timeout:
            exc = RequestTimeoutError("Request to the provider timed out.")
            if on_error is not None:
                on_error(exc)
            else:
                raise exc from None
            return "".join(chunks)
        except requests.HTTPError as exc:
            try:
                self._map_error(exc)
            except TutorError as mapped:
                if on_error is not None:
                    on_error(mapped)
                else:
                    raise mapped from None
            return "".join(chunks)
        except TutorError as exc:
            if on_error is not None:
                on_error(exc)
            else:
                raise exc from None
            return "".join(chunks)
        except requests.RequestException as exc:
            err = ProviderError(f"Network error: {exc}")
            if on_error is not None:
                on_error(err)
            else:
                raise err from None
            return "".join(chunks)

        full = "".join(chunks).strip()
        if on_done is not None:
            on_done(full)
        return full
