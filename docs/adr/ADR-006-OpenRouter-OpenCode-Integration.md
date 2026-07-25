# ADR-006 — OpenRouter + OpenCode Integration

**Context:** Beyond OpenAI, AnkiTutor launches with support for **OpenRouter** and **OpenCode** (two variants: Zen and Go), all via REST API.

## Decision

All four providers implement the same `LLMProvider.chat(...)` / `chat_stream(...)` interface (see ADR-001). Differences are only in endpoint + auth header (and, for OpenRouter, optional extra headers):

| Provider (id) | Base URL (`/chat/completions`) | Auth |
|---|---|---|
| OpenAI (`openai`) | `https://api.openai.com/v1` | `Authorization: Bearer <key>` |
| OpenRouter (`openrouter`) | `https://openrouter.ai/api/v1` | `Authorization: Bearer <key>` + `HTTP-Referer` + `X-Title` |
| OpenCode Zen (`opencode-zen`) | `https://opencode.ai/zen/v1` | `Authorization: Bearer <key>` |
| OpenCode Go (`opencode-go`) | `https://opencode.ai/zen/go/v1` | `Authorization: Bearer <key>` |

- **OpenRouter**: OpenAI-compatible format; changes the base URL and adds `HTTP-Referer`/`X-Title` (recommended). Provides access to many models via a single token.
- **OpenCode (Zen / Go)**: cloud REST API, requires key + credits. Two variants with separate model catalogues and billing, both sharing the OpenAI-compatible format — they only override `base_url`.

## Alternatives

- OpenCode via CLI (subprocess) — rejected: REST is simpler to abstract in the Strategy and doesn't block the Anki process.

## Rationale

- **Modularity:** `BaseHTTPProvider` (Template Method) absorbs 90% of the code; each provider only overrides `base_url` + headers.
- **User choice:** OpenAI (simple), OpenRouter (model variety), OpenCode (own model / cost alternative).
- **Cost/privacy:** all are cloud + key; the difference is price and available model, not locality.

## Status

Accepted. Implemented in M3 — `providers/openrouter.py` (`OpenRouterProvider`) and `providers/opencode.py` (`OpenCodeZenProvider` + `OpenCodeGoProvider`), registered in the factory.
