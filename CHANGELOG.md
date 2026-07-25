# Changelog

All notable changes to AnkiTutor are documented here.

## [1.0.0] - 2026-07-25

### Bug Fixes
- Lazy import requests so tests run without it
- Guard requests import so CI and network tests both pass
- Quebrar linha longa no import fallback (ruff E501)

### Features
- Add CI, setup and README
- Add AI tutor panel and chat GUI
- Add OpenRouter and OpenCode providers
- Streaming chat, direct modes, history and Q+A note save
- Side chat panel with Markdown bubbles and save preview
- Padronizar visual com tema nativo do Anki
- Split timestamps, add clear history, auto-create AnkiTutor field

### Miscellaneous
- Add addon manifest
- Ignore runtime config with API keys
- Add example config.json
- Ignore history.json and add PR doc
- Stop tracking PR doc and commands.md

### Testing
- Add provider and tutor unit tests
- Skip network tests when requests is not installed
- Cover streaming, direct modes, history and Q+A save
