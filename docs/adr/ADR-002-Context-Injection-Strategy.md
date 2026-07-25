# ADR-002 — Context Injection Strategy

**Context:** The AI needs to answer *based on the card*. We must decide how to deliver the card content (front + back) to the LLM.

## Decision

Inject the card as **delimited text inside the system prompt**, not as structured JSON.

Context format:

```
CARD CONTEXT:
Front: {front}
Back: {back}
---
Answer based ONLY on the CARD CONTEXT above.
```

Modes (`simplify`, `example`, `relate`) are extra instructions in the same system prompt, defined in `prompts.py`.

## Alternatives

- Structured JSON in the message body (more rigid, worse for small models).
- Send only the front (loses the back, which often has the answer).

## Rationale

- **Clean / simple:** text delimiter is robust across any model.
- **Token-efficient:** avoids verbose schema.
- **Modular:** `prompts.py` isolates templates; changing mode doesn't touch `tutor.py`.

## Status

Accepted.
