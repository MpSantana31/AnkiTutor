"""Smoke tests for ``gui`` (offline; full GUI runs only inside Anki).

The real ``QDialog``/``QTextBrowser``/``QThread`` are unavailable in CI (PyQt6
ships with Anki, not the test venv). We only assert the module imports cleanly
and wires the expected features (streaming worker, direct-mode input disabling,
Markdown rendering per ADR-007, save-to-note per M3), so a regression that
breaks importability is caught. Interactive rendering is covered manually in
Anki.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ADDON = Path(__file__).resolve().parent.parent


def _load_gui():
    if "anki_tutor" in sys.modules:
        return sys.modules["anki_tutor"]
    spec = importlib.util.spec_from_file_location("anki_tutor", _ADDON / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["anki_tutor"] = mod
    spec.loader.exec_module(mod)
    return sys.modules["anki_tutor"]


def test_gui_imports_and_exposes_panel():
    _load_gui()
    from anki_tutor import gui

    assert hasattr(gui, "TutorPanel")
    assert hasattr(gui, "TutorWorker")
    assert callable(gui.TutorPanel._on_save)
    assert callable(gui.TutorPanel._on_ask)


def test_build_conversation_markdown_renders_turns():
    _load_gui()
    from anki_tutor import gui

    turns = [
        (
            "What is strtok?",
            "explain",
            "It splits strings.",
            False,
            "2026-07-16T12:00:00Z",
            "2026-07-16T12:00:05Z",
        ),
        (
            "",
            "simplify",
            "Simpler: it splits strings.",
            False,
            "2026-07-16T12:01:00Z",
            "2026-07-16T12:01:03Z",
        ),
    ]
    md = gui.build_conversation_markdown(turns, gui.user_label)
    assert "**You**" in md
    assert "**You (simplify)**" in md
    assert "What is strtok?" in md
    assert "[simplify]" in md
    assert "It splits strings." in md
    assert "Simpler: it splits strings." in md
    assert "16/07" in md  # timestamp rendered
    assert "\n\n---\n\n" in md


def test_gui_wires_streaming_and_direct_modes():
    _load_gui()
    from anki_tutor import gui

    source = Path(gui.__file__).read_text(encoding="utf-8")
    assert "setMarkdown" in source
    assert "save-btn" in source
    # Streaming worker + direct-mode input disabling must be present.
    assert "TutorWorker" in source
    assert "setDisabled" in source
    # Direct modes come from prompts, not hardcoded.
    assert "DIRECT_MODES" in source
