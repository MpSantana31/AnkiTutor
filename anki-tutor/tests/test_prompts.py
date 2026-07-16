"""Tests for ``prompts`` module (offline)."""

from __future__ import annotations

from prompts import build_prompt


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
