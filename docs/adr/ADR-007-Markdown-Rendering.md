# ADR-007 — Markdown Rendering

**Context:** The LLM returns its answer in **Markdown** (headings, lists, bold, inline code). Previously `gui.py` used `output.setPlainText(answer)`, so Markdown appeared as **raw text** (asterisks, `#`, backticks). Hard to read and gives a prototype feel — unacceptable for a portfolio project.

## Decision

Render the response as Markdown using **`QTextBrowser.setMarkdown()`** (native to Qt 5.14+, present in PyQt6 bundled with Anki). Zero new dependencies.

- The answer widget (`answer-display`) was already a `QTextBrowser`; just changed `setPlainText` to `setMarkdown` in `_on_ask`.
- Transient state ("Thinking…") and error messages (`Error: …`) remain as plain text.

## Alternatives

- **MD → HTML with parser + `setHtml`** (applying the theme from `_STYLESHEET`): better visual result and control, but requires a Markdown parser (vendor `markdown` lib or write a mini-parser), since Anki embeds Python without third-party libs. Rejected in MVP for cost/dependency; can be revisited in M4 if `setMarkdown` proves limited.
- **Keep `setPlainText`**: rejected — raw text is the pain this ADR solves.

## Rationale

- **Trivial cost, high visual impact:** ~1 line of code, no deps.
- **Native:** `setMarkdown` ships with Anki's Qt; nothing to package/test extra.
- **Portfolio:** the rendered response is what the user sees and what appears in the demo/GIF.

## Known limitations

- `setMarkdown()` has partial support for **tables** and **code fences** (```); it handles headings, lists, bold/italic, and inline code well. If it becomes a problem, migrate to MD→HTML (the alternative above) in M4.

## Status

Accepted. Implemented in **M2** (before the MVP).
