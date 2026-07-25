# Changelog

All notable changes to AnkiTutor are documented here.

## [Unreleased]

### Added

- Architecture, testing, and security documentation in `docs/`.
- Architecture Decision Records published at `docs/adr/` (ADR-001 through ADR-009).
- `CHANGELOG.md` now generated with `git-cliff`.
- Full offline test suite with `FakeProvider` (91 tests, 78% coverage).
- CI now installs `requests` so provider tests run in CI.

### Fixed

- `config.schema.json` converted to proper JSON Schema (`$schema`, types, `enum`, `required`).

## [1.0.0] - unreleased

### Added

- Real SSE streaming — tokens appear in real time via `TutorWorker` (QThread),
  never freezing the Anki UI (ADR-003).
- Native Anki theme adaptation (light/dark via `theme_manager.var()`).
- Direct response modes — `simplify`, `example`, `relate` — ask
  automatically without user input.
- Per-card history — past Q&A is persisted in `history.json` and re-rendered
  when the panel reopens (ADR-008).
- "Save to note" button — writes the Q&A pair to the card's note field.
- OpenRouter and OpenCode (Zen/Go) providers.
- Side chat panel with Markdown rendering (`QTextBrowser.setMarkdown()`).

### Changed

- Config stored via Anki's `addonManager` (not `.env`).
- Error boundary: all provider failures map to `TutorError` subclasses and
  render as friendly in-chat messages (never crash Anki).

### Fixed

- UTF-8 decoding in SSE stream — accented characters (`você`, `não`) no
  longer display as mojibake.

## [0.2.0] - 2026-07-18

- Multi-provider support (OpenRouter, OpenCode Zen/Go).
- Streaming SSE, direct modes, history, and save-to-note features.
- Expanded offline test suite.

## [0.1.0] - 2026-07-16

- MVP with OpenAI provider.
- Chat panel GUI (PyQt6) with streaming.
- Error hierarchy (`TutorError`).
- Config dialog (provider, API key, model, language).
- CI with ruff + pytest.

## [0.0.1] - 2026-07-14

- Project scaffolding, repository setup, initial README.

---

*Generated with [git-cliff](https://git-cliff.org). To update for a new release:*

```bash
git tag vX.Y.Z
git-cliff --tag vX.Y.Z --output CHANGELOG.md
git add CHANGELOG.md && git commit -m "chore(release): vX.Y.Z"
```
