# ADR-008 — History Storage

**Context:** Users want to review past questions. History is **per card**: reopening the panel for a card should show previous Q&A for that card. Currently each question is ephemeral — closing the panel loses it.

## Scope

- **Grouping:** by **card** (`card_id`).
- Each entry stores: `card_id`, `deck_id`, `question`, `answer`, `mode`, `provider`, `model`, `timestamp`.
- `deck_id` is stored from the start to allow a future deck-level view without data migration.

## Decision

### Persistence

Store history in a **JSON file in the add-on directory** (outside `config.json`/`meta.json`), keyed by `card_id`:

```json
{
  "1699999999": [
    {
      "question": "...",
      "answer": "...",
      "mode": "explain",
      "provider": "openai",
      "model": "gpt-4o-mini",
      "deck_id": 42,
      "timestamp": "2026-07-16T12:00:00Z"
    }
  ]
}
```

- Simple, no schema/migration; easy to test offline.
- **Not** committed to the repository (contains user card content) — same privacy treatment as `meta.json` (`.gitignore`).

### M2 preparation (avoids rework)

In M2, `tutor.ask` was changed to return a **structured object** instead of `str`:

```python
@dataclass
class TutorAnswer:
    answer: str
    question: str
    mode: str
    card_id: int | None
    deck_id: int | None
    provider: str
    model: str
    timestamp: str
```

In M3, history simply **consumes** this object (appends to JSON), without refactoring `tutor`/`gui`. `gui.py` still displays `answer.answer` (rendered as Markdown — ADR-007).

## Alternatives

- **`mw.col` / custom Anki collection data:** integrated with Anki sync, but couples to the collection schema and complicates offline testing. Rejected for now.
- **Custom SQLite:** overkill for the expected volume (a few questions per card).
- **Save as note field** (the "save to card" UX idea): a *separate* feature (persisting in the card itself), not navigable history. Can coexist later.

## Rationale

- **MVP doesn't depend on it:** the core value ("ask → understand on the spot") is already delivered without history → left for M3.
- **Cheap prep in M2:** returning structured data costs ~zero now and avoids refactoring in M3.
- **Privacy:** local data, never versioned.

## Status

Accepted. **Prep (structured data) in M2; persistent history + UI in M3.**
