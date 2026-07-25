# Architecture

## Overview

AnkiTutor is an Anki add-on that adds an AI tutor to the card reviewer. The user clicks a button, asks a question about the current card, and receives a streamed Markdown answer from an LLM provider — without freezing the Anki UI.

## File structure

```
anki-tutor/
├── __init__.py          Entry point: hooks, menu, shortcut
├── manifest.json        Add-on metadata
├── config.json          Default config (example, no real keys)
├── config.py            Config dialog (QDialog) + live model fetch
├── tutor.py             Orchestrator: builds context, calls provider
├── gui.py               Chat panel (QDialog) + TutorWorker (streaming)
├── prompts.py           System prompt builder (context + mode + language)
├── utils.py             Card extraction, HTML stripping, save-to-note
├── history.py           Per-card history in history.json
├── errors.py            TutorError hierarchy (ADR-005)
├── providers/           Strategy/Factory for LLM backends
│   ├── base.py          LLMProvider ABC + BaseHTTPProvider
│   ├── factory.py       create_provider / register_provider
│   ├── openai.py        OpenAIProvider
│   ├── openrouter.py    OpenRouterProvider
│   └── opencode.py      OpenCodeZenProvider + OpenCodeGoProvider
└── tests/               Offline test suite (pytest)
```

## Data flow

```
[Reviewer Card]
    │  front + back (extracted by utils.py)
    ▼
[tutor.py] ──context──► [LLM Provider] ──token stream──► on_token / on_done / on_error
    │                (OpenAI / OpenRouter / OpenCode)
    │  TutorAnswer (answer, question, mode, card_id, deck_id, provider, model, ts)
    ▼
[gui.py] → worker off UI thread receives tokens → renders Markdown incrementally
    → appends to per-card JSON history (history.py)
```

1. Hook injects "Ask AI" button into Anki's reviewer
2. On click, `utils.py` extracts front/back from the current card
3. `tutor.py` builds the prompt with context + question + mode
4. Calls the provider in streaming mode (`chat_stream`); tokens arrive via `on_token`
5. `gui.py` renders the response as **Markdown** (ADR-007); errors become friendly text
6. The Q&A pair is saved to per-card history (ADR-008)

## Component diagram

```mermaid
flowchart TD
    Anki[Anki / Reviewer] -->|Ask AI button / shortcut| Init[__init__.py]
    Init -->|opens panel| GUI[gui.py\nChat Panel]
    Init -->|Tools menu| Config[config.py\nConfig Dialog]
    GUI -->|context+question+mode| Tutor[tutor.py\nOrchestrator]
    Tutor -->|create_provider| Factory[factory.py]
    Factory -->|instantiates| Provider[LLMProvider\nABC - Strategy]
    Provider -->|POST /chat/completions| Net[(Provider API\nOpenAI / OpenRouter / OpenCode)]
    Provider -->|TutorError| Err[errors.py\nError Boundary]
    Err -->|friendly text| GUI
    Tutor -->|TutorAnswer| GUI
    GUI -->|setMarkdown| MD[Markdown Render\nADR-007]
    GUI -.->|append| Hist[(JSON History\nper card_id — ADR-008)]
    Config -->|provider, model, language, api_keys| Cfg[(Anki config\nmeta.json)]
    Tutor -->|build_prompt| Prompts[prompts.py]
    GUI -->|extract card| Utils[utils.py\nextract_card]
    Utils -->|front+back| Tutor
```

## Class diagram (Strategy + Factory + Template Method)

```mermaid
classDiagram
    class LLMProvider {
        <<abstract>>
        +chat(context, question, mode) str
        +chat_stream(context, question, mode, on_token, on_done, on_error) str
    }
    class BaseHTTPProvider {
        <<abstract>>
        -base_url: str
        -auth_scheme: str
        -api_key: str
        -model: str
        -language: str
        #_extra_headers() dict
        +chat(context, question, mode) str
        +chat_stream(context, question, mode, on_token, on_done, on_error) str
    }
    class OpenAIProvider {
        -base_url = api.openai.com/v1
    }
    class OpenRouterProvider {
        -base_url = openrouter.ai/api/v1
        #_extra_headers() HTTP-Referer, X-Title
    }
    class OpenCodeZenProvider {
        -base_url = opencode.ai/zen/v1
    }
    class OpenCodeGoProvider {
        -base_url = opencode.ai/zen/go/v1
    }
    class ProviderFactory {
        +create_provider(name, config) LLMProvider
        +register_provider(name, cls)
    }
    class TutorError {
        <<exception>>
    }
    class AuthError
    class RateLimitError
    class TimeoutError
    class ProviderError
    class ConfigError

    LLMProvider <|-- BaseHTTPProvider
    BaseHTTPProvider <|-- OpenAIProvider
    BaseHTTPProvider <|-- OpenRouterProvider
    BaseHTTPProvider <|-- OpenCodeZenProvider
    BaseHTTPProvider <|-- OpenCodeGoProvider
    ProviderFactory ..> LLMProvider : creates
    TutorError <|-- AuthError
    TutorError <|-- RateLimitError
    TutorError <|-- TimeoutError
    TutorError <|-- ProviderError
    TutorError <|-- ConfigError
```

## Key patterns

| Pattern | Where | Purpose |
|---|---|---|
| **Strategy** | `LLMProvider` + 4 implementations | Swap LLM backends without changing UI |
| **Factory** | `create_provider()` / `register_provider()` | Select provider by config name |
| **Template Method** | `BaseHTTPProvider.chat()` + `_extra_headers()` hook | Share HTTP logic across providers |
| **Observer** | `chat_stream()` callbacks (`on_token`/`on_done`/`on_error`) | Stream tokens to the GUI without coupling |
| **Error Boundary** | `TutorError` hierarchy caught in `gui.py` | Never crash Anki on API failures |

## Constraints

- Runs inside Anki's embedded Python (stdlib + `requests`/`httpx` only)
- PyQt6 already bundled with Anki — use for GUI, don't install
- Config managed by Anki's `addonManager`, not `.env`
- Tests must run offline, without Anki (`FakeProvider`)
