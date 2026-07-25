"""Tests for ``utils.extract_card`` / ``utils.extract_card_meta`` (offline)."""

from __future__ import annotations

from utils import (
    build_save_text,
    extract_card,
    extract_card_meta,
    save_answer_to_note,
)


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


def test_card_meta_from_fakecard():
    class FakeCard:
        card_id = 7
        deck_id = 99

    assert extract_card_meta(FakeCard()) == (7, 99)


def test_card_meta_from_real_card():
    class Card:
        id = 123
        did = 456

    assert extract_card_meta(Card()) == (123, 456)


def test_card_meta_none_when_missing():
    class Card:
        pass

    assert extract_card_meta(Card()) == (None, None)
    assert extract_card_meta(None) == (None, None)


def test_save_answer_to_existing_ankitutor_field():
    # dict-style fields (test fixture); Note is dict-like so note["name"] works.
    class Note(dict):
        fields = None  # type: ignore[assignment]

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.fields = self

        def flush(self):
            pass

    note = Note({"Front": "q", "Back": "a", "AnkiTutor": ""})

    class Card:
        def note(self):
            return note

    msg = save_answer_to_note(Card(), "explain text")
    assert msg.message == "Saved to note."
    assert note["AnkiTutor"] == "explain text"


def test_save_answer_appends_when_field_has_content():
    class Note(dict):
        fields = None  # type: ignore[assignment]

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.fields = self

        def flush(self):
            pass

    note = Note({"Front": "q", "AnkiTutor": "old"})

    class Card:
        def note(self):
            return note

    save_answer_to_note(Card(), "new")
    assert "old" in note["AnkiTutor"]
    assert "new" in note["AnkiTutor"]


def test_save_answer_fails_when_no_ankitutor_field(tmp_path, monkeypatch):
    """Now requires 'AnkiTutor' field; no more fallback to last field."""
    from anki_tutor.utils import save_answer_to_note

    class Note(dict):
        fields = None  # type: ignore[assignment]

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.fields = self

        def flush(self):
            pass

    # Real Anki notes expose fields as a list but support dict-like access.
    field_names = ["Front", "Back"]
    values = ["q", "a"]

    class NoteList:
        fields = values

        def keys(self):
            return list(field_names)

        def __getitem__(self, key):
            return values[field_names.index(key)]

        def __setitem__(self, key, value):
            values[field_names.index(key)] = value

        def flush(self):
            pass

    note = NoteList()

    class Card:
        def note(self):
            return note

    msg = save_answer_to_note(Card(), "explain text")
    assert "AnkiTutor" in msg.message
    assert "add it" in msg.message.lower()
    # Nothing was saved — Back field must be untouched.
    assert note["Back"] == "a"


def test_save_answer_no_note_returns_message():
    class Card:
        pass

    assert "Could not access" in save_answer_to_note(Card(), "x").message


def test_save_answer_no_fields_returns_message():
    class Note:
        fields = []

        def flush(self):
            pass

    class Card:
        def note(self):
            return Note()

    msg = save_answer_to_note(Card(), "x")
    # Without any fields, _resolve_target_field returns None, then
    # _ensure_anki_tutor_field fails (no mw in tests), so we get the
    # "no AnkiTutor field" message.
    assert "AnkiTutor" in msg.message


def test_build_save_text_combines_question_and_answer():
    text = build_save_text("What is strtok?", "It splits strings.", "explain")
    assert "**Q:** What is strtok?" in text
    assert "**A:** It splits strings." in text


def test_build_save_text_direct_mode_uses_mode_label():
    text = build_save_text("", "Simpler: it splits.", "simplify")
    assert "**Q:** [simplify]" in text
    assert "**A:** Simpler: it splits." in text
