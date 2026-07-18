"""Domain fixtures for tests, with no dependency on Anki or the network.

Provides a ``FakeCard`` (front/back) and a ``FakeProvider`` implementing
``LLMProvider`` without making HTTP calls — used across the whole test suite.
"""

from __future__ import annotations


class FakeCard:
    """Minimal card with front/back for ``utils``/``tutor`` tests."""

    def __init__(
        self,
        front: str = "Capital of France?",
        back: str = "Paris",
        card_id: int | None = 1,
        deck_id: int | None = 42,
    ) -> None:
        self.front = front
        self.back = back
        self.card_id = card_id
        self.deck_id = deck_id


class FakeProvider:
    """Fake ``LLMProvider`` implementation — never touches the network."""

    name = "fake"
    model = "fake-model"

    def chat(
        self,
        context: str,
        question: str,
        mode: str = "explain",
    ) -> str:
        return f"[fake] {mode}: {question} | ctx={context}"

    def chat_stream(
        self,
        context: str,
        question: str,
        mode: str = "explain",
        on_token=None,
        on_done=None,
        on_error=None,
    ) -> str:
        text = self.chat(context, question, mode)
        if on_token is not None:
            on_token(text)
        if on_done is not None:
            on_done(text)
        return text
