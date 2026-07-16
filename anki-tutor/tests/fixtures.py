"""Domain fixtures for tests, with no dependency on Anki or the network.

Provides a ``FakeCard`` (front/back) and a ``FakeProvider`` implementing
``LLMProvider`` without making HTTP calls — used across the whole test suite.
"""

from __future__ import annotations


class FakeCard:
    """Minimal card with front/back for ``utils``/``tutor`` tests."""

    def __init__(self, front: str = "Capital of France?", back: str = "Paris") -> None:
        self.front = front
        self.back = back


class FakeProvider:
    """Fake ``LLMProvider`` implementation — never touches the network."""

    name = "fake"

    def chat(
        self,
        context: str,
        question: str,
        mode: str = "explain",
    ) -> str:
        return f"[fake] {mode}: {question} | ctx={context}"
