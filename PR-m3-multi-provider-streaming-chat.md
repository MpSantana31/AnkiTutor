# feat: streaming chat, direct modes, per-card history and Q+A note save

## Objective

Add SSE streaming across providers, direct response modes (`simplify`/`example`/
`relate`) that need no user input, a persistent per-card chat history, and a
"Save to note" button that records **question + answer** into the card's last
field. Fix UTF-8 mojibake in SSE decoding and ensure the note is committed to
disk.

## Changes

- `providers/base.py`: `chat_stream()` with OpenAI-style SSE parsing and UTF-8
  decode; explicit `on_token`/`on_done`/`on_error` callbacks.
- `tutor.py`: `ask_stream()` with streaming + history persistence; `TutorAnswer`
  dataclass; direct-mode question inference.
- `prompts.py`: `DIRECT_MODES` + `implicit_question(mode, language)` (i18n).
- `history.py` (new): load/append chat history by `card_id` in `history.json`
  (ignored by git).
- `gui.py`: `TutorWorker(QThread)` + side chat panel with Markdown bubbles;
  renders accumulated history and live streaming; save button shows field + preview.
- `utils.py`: `save_answer_to_note()` writes Q+A via `build_save_text` and calls
  `col.save()` so the change is persisted. Accepts `note.fields` as a list.
- Tests: new `test_history.py`, `test_gui.py`; expanded provider/tutor/prompt/
  utils tests + fixtures.

## Evidence

- `pytest anki-tutor/tests -q` → all pass.
- `ruff check` + `ruff format --check` → clean.
- SSE UTF-8 regression test guarantees `você` (not `vocÃª`).

## Notes

- `gemini.py`/`claude.py` intentionally excluded.
- `gui.py` runs only inside Anki (PyQt6); GUI tests are import/smoke level.
