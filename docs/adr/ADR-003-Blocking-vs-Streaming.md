# ADR-003 — Blocking vs Streaming

**Context:** The LLM response can be delivered all at once (blocking) or in real-time (streaming/SSE).

## Decision

**Implementation = Streaming.** `gui.py` calls `provider.chat_stream(...)` and receives tokens in real-time via the `on_token` callback, progressively rendering the response (incremental Markdown) without freezing the Anki UI.

The **Observer** pattern was effectively adopted: `provider.chat_stream(...)` emits `on_token` / `on_done` / `on_error` events that the panel subscribes to. The blocking `provider.chat(...)` remains available for tests, but the user flow uses streaming.

## Alternatives

- Blocking in the MVP (simple, deterministic, easy to mock) — rejected for the user flow: long responses froze the Anki window and felt like a crash.

## Rationale

- **UX:** tokens appear in real-time, the UI never freezes (even with 500+ token responses).
- **Isolation:** streaming runs off the UI thread (worker/QThread); `on_token` only schedules a `QTextBrowser` repaint. The error boundary still catches failures at stream end (`on_error`).
- **Clean code:** `LLMProvider` exposes `chat` (blocking, for tests) and `chat_stream` (callback); `gui.py` orchestrates via a worker, keeping responsibilities separate.

## Status

Accepted (real streaming in the user flow; blocking `chat` kept for tests/CI).
