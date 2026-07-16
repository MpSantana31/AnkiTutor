"""Concrete OpenAI provider (MVP — ADR-001)."""

from __future__ import annotations

from .base import BaseHTTPProvider


class OpenAIProvider(BaseHTTPProvider):
    name = "openai"
    base_url = "https://api.openai.com/v1"
