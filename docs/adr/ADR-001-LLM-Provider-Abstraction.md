# ADR-001 — LLM Provider Abstraction

**Context:** AnkiTutor must support multiple LLM backends (OpenAI, OpenRouter, OpenCode) and allow the user to switch providers via configuration without rewriting UI logic.

## Decision

Use **Strategy** for providers + **Factory** for selection, and **Template Method** for shared HTTP logic.

- `LLMProvider` (ABC) defines `chat(context, question, mode) -> str` (blocking, for tests) and `chat_stream(context, question, mode, on_token, on_done, on_error)` (streaming, user flow — see ADR-003).
- Each provider (`OpenAIProvider`, `OpenRouterProvider`, `OpenCodeProvider`) is a concrete strategy.
- `ProviderFactory.create(name, config)` injects the right provider.
- `BaseHTTPProvider` (Template Method) implements: building headers, JSON body, mapping errors → `TutorError`.

## Alternatives

- Direct if/else in `tutor.py` per provider (coupled, hard to test).
- Heavy Dependency Injection framework (overkill for an Anki add-on).

## Rationale

- **Modularity / clean code:** each provider isolated, testable, and swappable.
- **Extensibility:** adding a provider = new class, no UI changes.
- **Testability:** `tutor.py` depends on the abstraction → easy to mock in tests.

## Status

Accepted. Implemented in M2 (MVP with OpenAI) and M3 (remaining providers).
