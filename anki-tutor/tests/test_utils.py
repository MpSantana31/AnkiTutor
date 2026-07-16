"""Tests for ``utils.extract_card`` (offline)."""

from __future__ import annotations

from utils import extract_card


def test_none_returns_empty():
    assert extract_card(None) == ("", "")


def test_fakecard_attributes():
    class FakeCard:
        front = "<b>Capital?</b>"
        back = "Paris"

    front, back = extract_card(FakeCard())
    assert "Capital?" in front
    assert back == "Paris"


def test_real_note_fields():
    class Note:
        fields = {"Front": "<p>2+2?</p>", "Back": "<i>4</i>"}

    class Card:
        def note(self):
            return Note()

    front, back = extract_card(Card())
    assert front == "2+2?"
    assert back == "4"


def test_note_field_order_fallback():
    class Note:
        fields = {"Term": "<p>dog</p>", "Definition": "<i>animal</i>"}

    class Card:
        def note(self):
            return Note()

    front, back = extract_card(Card())
    assert front == "dog"
    assert back == "animal"
