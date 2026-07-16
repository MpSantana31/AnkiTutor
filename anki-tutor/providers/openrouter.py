"""Concrete OpenRouter provider (M3 — ADR-001/ADR-006)."""

from __future__ import annotations

from .base import BaseHTTPProvider


class OpenRouterProvider(BaseHTTPProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"

    def _extra_headers(self) -> dict[str, str]:
        # OpenRouter asks for identifying headers (optional but recommended).
        return {
            "HTTP-Referer": "https://github.com/MpSantana31/AnkiTutor",
            "X-Title": "AnkiTutor",
        }
