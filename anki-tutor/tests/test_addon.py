"""Minimal coverage tests for the core modules (MVP).

Each core module (errors, prompts, utils, providers, tutor) will get its own
test file. This file holds cross-cutting helpers and validations that do not
depend on any specific module.

Tests are 100% offline: they do not import ``aqt``/``anki`` and make no network
calls.
"""

from __future__ import annotations

import json
from pathlib import Path

ADDON_DIR = Path(__file__).resolve().parent.parent


def test_manifest_is_valid_json() -> None:
    manifest = ADDON_DIR / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["package"] == "anki-tutor"
    assert data["name"] == "AnkiTutor"
    assert "version" in data


def test_no_secret_in_manifest() -> None:
    text = (ADDON_DIR / "manifest.json").read_text(encoding="utf-8")
    assert "api_key" not in text
    assert "sk-" not in text
