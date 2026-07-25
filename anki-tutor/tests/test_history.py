"""Tests for ``history`` persistence (offline, no network, no Anki)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ADDON = Path(__file__).resolve().parent.parent


def _load_addon():
    if "anki_tutor" in sys.modules:
        return sys.modules["anki_tutor"]
    spec = importlib.util.spec_from_file_location("anki_tutor", _ADDON / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["anki_tutor"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_answer(card_id: int | None = 1, deck_id: int | None = 42):
    from anki_tutor.tutor import TutorAnswer

    return TutorAnswer(
        answer="Paris",
        question="Capital of France?",
        mode="explain",
        card_id=card_id,
        deck_id=deck_id,
        provider="openai",
        model="gpt-4o-mini",
        asked_at="2026-07-16T12:00:00Z",
        answered_at="2026-07-16T12:00:05Z",
    )


def test_load_missing_returns_empty(tmp_path, monkeypatch):
    _load_addon()
    from anki_tutor.history import load_history

    monkeypatch.setattr("anki_tutor.history.HISTORY_PATH", tmp_path / "history.json")
    assert load_history(1) == []


def test_append_then_load_roundtrip(tmp_path, monkeypatch):
    _load_addon()
    from anki_tutor.history import append_history, load_history

    monkeypatch.setattr("anki_tutor.history.HISTORY_PATH", tmp_path / "history.json")
    append_history(_make_answer(card_id=1))
    entries = load_history(1)
    assert len(entries) == 1
    assert entries[0]["answer"] == "Paris"
    assert entries[0]["question"] == "Capital of France?"
    assert entries[0]["mode"] == "explain"
    assert entries[0]["provider"] == "openai"
    assert entries[0]["model"] == "gpt-4o-mini"


def test_history_keyed_by_card_id(tmp_path, monkeypatch):
    _load_addon()
    from anki_tutor.history import append_history, load_history

    monkeypatch.setattr("anki_tutor.history.HISTORY_PATH", tmp_path / "history.json")
    append_history(_make_answer(card_id=1))
    append_history(_make_answer(card_id=2))
    assert len(load_history(1)) == 1
    assert len(load_history(2)) == 1


def test_corrupt_file_returns_empty(tmp_path, monkeypatch):
    _load_addon()
    from anki_tutor.history import load_history

    path = tmp_path / "history.json"
    path.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr("anki_tutor.history.HISTORY_PATH", path)
    assert load_history(1) == []


def test_append_without_card_id_is_noop(tmp_path, monkeypatch):
    _load_addon()
    from anki_tutor.history import append_history

    monkeypatch.setattr("anki_tutor.history.HISTORY_PATH", tmp_path / "history.json")
    append_history(_make_answer(card_id=None))
    assert not (tmp_path / "history.json").exists()


def test_load_history_none_returns_empty(tmp_path, monkeypatch):
    _load_addon()
    from anki_tutor.history import load_history

    monkeypatch.setattr("anki_tutor.history.HISTORY_PATH", tmp_path / "history.json")
    assert load_history(None) == []


def test_clear_history_removes_all_entries(tmp_path, monkeypatch):
    _load_addon()
    from anki_tutor.history import append_history, clear_history, load_history

    monkeypatch.setattr("anki_tutor.history.HISTORY_PATH", tmp_path / "history.json")
    append_history(_make_answer(card_id=1))
    append_history(_make_answer(card_id=1))
    assert len(load_history(1)) == 2
    clear_history(1)
    assert load_history(1) == []


def test_clear_history_unknown_card_is_noop(tmp_path, monkeypatch):
    _load_addon()
    from anki_tutor.history import clear_history

    monkeypatch.setattr("anki_tutor.history.HISTORY_PATH", tmp_path / "history.json")
    clear_history(999)  # should not raise


def test_clear_history_none_is_noop(tmp_path, monkeypatch):
    _load_addon()
    from anki_tutor.history import clear_history

    monkeypatch.setattr("anki_tutor.history.HISTORY_PATH", tmp_path / "history.json")
    clear_history(None)  # should not raise
