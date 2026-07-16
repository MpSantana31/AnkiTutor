"""Shared pytest configuration.

Exposes ``FakeProvider``/``FakeCard`` as fixtures and ensures the add-on
folder (``anki-tutor``) is on ``sys.path`` so core modules can be imported
directly (without a separate ``anki_tutor`` package).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

ADDON_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
if str(ADDON_DIR) not in sys.path:
    sys.path.insert(0, str(ADDON_DIR))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_fixtures = _load_module("anki_tutor_fixtures", TESTS_DIR / "fixtures.py")

FakeCard = _fixtures.FakeCard
FakeProvider = _fixtures.FakeProvider

__all__ = ["FakeCard", "FakeProvider"]


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def fake_card() -> FakeCard:
    return FakeCard()


@pytest.fixture
def addon_path() -> Path:
    return ADDON_DIR


def test_environment() -> None:
    """Smoke: ensures the add-on directory exists and has a manifest."""
    assert (ADDON_DIR / "manifest.json").exists()
    assert os.path.isdir(ADDON_DIR)
