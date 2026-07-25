# Testing Strategy

## Principle

100% offline — no network and no running Anki instance. `LLMProvider` is an abstraction, so tests use a **FakeProvider** instead of mocking `requests`.

```python
class FakeProvider(LLMProvider):
    def chat(self, context, question, mode):
        return f"[fake] {mode}: {question}"
```

## What is tested

| Layer | What | File |
|---|---|---|
| `prompts.py` | `build_prompt` injects front/back and mode; `DIRECT_MODES`/`implicit_question` | `test_prompts.py` |
| `utils.py` | Card front/back extraction; `save_answer_to_note`; `build_save_text` | `test_utils.py` |
| `factory.py` | Valid name → provider; invalid name → `ConfigError`; empty model | `test_providers.py` |
| `providers/` | SSE parse, error→`TutorError`, UTF-8, `chat_stream` callbacks | `test_providers.py` |
| `tutor.py` | `ask`/`ask_stream` with `FakeProvider`; direct mode inference | `test_tutor.py` |
| `history.py` | Load/append/roundtrip/corrupt/keyed-by-card | `test_history.py` |
| `config.py` | Defaults, roundtrip, Anki persistence, `fetch_models` fallback | `test_config.py` |
| `errors.py` | Hierarchy + `user_message` + no shadow of builtins | `test_errors.py` |
| `gui.py` | (Smoke) import + static checks; no PyQt6/Anki needed | `test_gui.py` |
| `addon` | Valid manifest + secret scan (no api_key in manifest) | `test_addon.py` |

## Running

```bash
pytest --cov=anki-tutor --cov-report=term-missing
```

CI runs the same command with `ruff check` and `ruff format --check` as gates.

## Fixtures

```python
class FakeCard:
    def __init__(self):
        self.front = "Capital of France?"
        self.back = "Paris"
        self.card_id = 1
        self.deck_id = 42
```

## Coverage targets

- `prompts.py`, `utils.py`, `factory.py`, `errors.py` → **100%**
- `tutor.py` → **100%** (with FakeProvider)
- `providers/base.py` → **90%+**
- `gui.py` → smoke test (import + static assertions)
- `__init__.py`, `config.py` (dialog) → Anki-only, tested manually
