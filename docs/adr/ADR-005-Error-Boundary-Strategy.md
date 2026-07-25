# ADR-005 — Error Boundary Strategy

**Context:** API failures (401, 429, timeout, parse) must not crash Anki or block the review hook.

## Decision

**Error Boundary via custom exception + friendly message.** All provider calls raise `TutorError` (subclass of `Exception`). `gui.py` catches it and displays a readable message in the response panel itself — the exception never propagates to the Anki hook.

Hierarchy:

```
TutorError (base)
├── AuthError       # 401
├── RateLimitError  # 429
├── TimeoutError    # request timeout
├── ProviderError   # 5xx / parse
└── ConfigError     # missing/invalid config (e.g. no API key)
```

## Alternatives

- `print` to console (user doesn't see it, hides bugs).
- Let the exception propagate (crashes Anki → poor experience).

## Rationale

- **Robustness:** Anki remains usable even if the AI fails.
- **UX:** clear message tells the user what to do (e.g. "Invalid API key").
- **Clean:** typed errors are easy to test.

## Status

Accepted.
