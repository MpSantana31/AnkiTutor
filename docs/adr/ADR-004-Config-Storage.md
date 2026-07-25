# ADR-004 — Config Storage

**Context:** The add-on needs persistent and secure configuration (provider, model, language, API keys).

## Decision

Use **Anki-managed config** (`mw.addonManager.getConfig()` / `writeConfig()`), with a fallback to the local `config.json` outside Anki (tests/CI).

- No `.env` (Anki does not load .env from add-ons).
- No custom storage in `%APPDATA%` (duplicates logic).
- Default config comes from `config.json`; at runtime Anki persists in `meta.json` (`~/Anki2/addons21/anki-tutor/`). `meta.json` holds the real keys and is **never** versioned (it's in `.gitignore`).

### Config format

API keys are stored **per provider** in an `api_keys` dict, to never mix keys from different providers:

```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "language": "en",
  "api_keys": {
    "openai": "",
    "openrouter": "",
    "opencode-zen": "",
    "opencode-go": ""
  }
}
```

The config dialog (`config.py`) also populates the model combo live via `fetch_models(provider, api_key)` (each provider's `/models` endpoint), falling back to a local catalogue when the network fails.

## Alternatives

- `.env` + `python-dotenv` (doesn't work well embedded in Anki).
- Custom SQLite (overkill).

## Rationale

- **Anki standard:** respects Anki's config lifecycle and UI.
- **Secure:** Anki isolates the add-on; the key is not plain text in the repo root.
- **Simple:** no extra dependencies.

## Note

Donation links (Ko-fi/GitHub Sponsors/Buy Me a Coffee) are **not** in config: they are constants in code (`support.py`) — see ADR-009.

## Status

Accepted.
