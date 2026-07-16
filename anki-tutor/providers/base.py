"""LLM provider abstraction (ADR-001 — Strategy + Template Method).

``LLMProvider`` is the strategy interface; ``BaseHTTPProvider`` implements the
shared HTTP logic (headers, payload, error mapping). Concrete providers only
override ``base_url`` and, when needed, ``_extra_headers``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from .. import prompts
from ..errors import (
    AuthError,
    ProviderError,
    RateLimitError,
    RequestTimeoutError,
)


class LLMProvider(ABC):
    """Strategy interface for an LLM backend."""

    name: str = "base"

    @abstractmethod
    def chat(self, context: str, question: str, mode: str = "explain") -> str:
        """Return the model's answer given the card context and a question."""


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

    def _map_error(self, exc: requests.HTTPError) -> None:
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
