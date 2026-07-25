# Security & Privacy

## API key

- Stored **only** in Anki-managed config (`meta.json` via `mw.addonManager`), never in the code or committed files.
- The example `config.json` in the repository contains empty strings — real keys go into `meta.json` at runtime (which is `.gitignore`d).
- Keys are stored **per provider** in an `api_keys` dict, so they are never mixed or shared between providers.

## What data leaves the machine

Only the card's **front and back text** plus the **user's question** are sent to the chosen LLM provider. No personal information (deck names, review statistics, tags, etc.) is transmitted.

All four supported providers are cloud-based:
- **OpenAI** — data sent to `api.openai.com`
- **OpenRouter** — data sent to `openrouter.ai`
- **OpenCode Zen / Go** — data sent to `opencode.ai`

The add-on makes **no other external calls** besides the single LLM provider API endpoint.

## History

Per-card Q&A history is stored locally in `history.json` inside the add-on directory. This file is never committed to the repository (`.gitignore`d) and is not synced by AnkiWeb.

## Add-on permissions

The add-on does not:
- Collect telemetry or analytics
- Log API keys or card content
- Open pop-ups or external links without user action
- Access files outside its own directory

## Best practices

- Short request timeout (30s) so a slow provider never freezes Anki
- All provider errors are caught and shown as friendly in-chat messages — never a traceback or crash
- The **Tools > Support AnkiTutor…** dialog is opt-in (menu action), never triggered automatically
