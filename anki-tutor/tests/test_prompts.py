"""Tests for ``prompts`` module (offline)."""

from __future__ import annotations

from prompts import DIRECT_MODES, build_prompt, implicit_question


def test_prompt_contains_context():
    p = build_prompt("Front: A\nBack: B", mode="explain", language="pt-BR")
    assert "Front: A" in p
    assert "Back: B" in p
    assert "pt-BR" in p


def test_prompt_modes():
    base = build_prompt("ctx", mode="explain")
    assert "clearly and concisely" in base
    assert "beginner" in build_prompt("ctx", mode="simplify")
    assert "practical" in build_prompt("ctx", mode="example")
    assert "relate" in build_prompt("ctx", mode="relate")


def test_unknown_mode_falls_back_to_explain():
    p = build_prompt("ctx", mode="nope")
    assert "clearly and concisely" in p


def test_direct_modes_exclude_explain():
    assert "explain" not in DIRECT_MODES
    assert set(DIRECT_MODES) == {"simplify", "example", "relate"}


def test_implicit_question_per_language():
    assert implicit_question("simplify", "pt-BR") == (
        "Explique este card como se estivesse ensinando um iniciante."
    )
    assert implicit_question("example", "en").startswith("Explain this card")
    assert implicit_question("relate", "es").startswith("Explica esta tarjeta")


def test_implicit_question_falls_back_to_english():
    assert implicit_question("simplify", "xx").startswith("Explain this card")


def test_implicit_question_explain_is_generic():
    assert implicit_question("explain", "en") == "Explain this card."
