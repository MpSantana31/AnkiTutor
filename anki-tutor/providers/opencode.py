"""Concrete OpenCode providers (M3 — ADR-006).

OpenCode exposes two distinct API variants with separate model catalogues and
billing: "Zen" and "Go". They share the OpenAI-compatible request/response
shape, so both only override ``base_url``.
"""

from __future__ import annotations

from .base import BaseHTTPProvider


class OpenCodeZenProvider(BaseHTTPProvider):
    name = "opencode-zen"
    base_url = "https://opencode.ai/zen/v1"


class OpenCodeGoProvider(BaseHTTPProvider):
    name = "opencode-go"
    base_url = "https://opencode.ai/zen/go/v1"
