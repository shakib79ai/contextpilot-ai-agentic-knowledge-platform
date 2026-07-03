# Human-in-the-Loop Review

ContextPilot AI never lets a low-confidence answer reach an end user unchecked. Instead of guessing, it escalates.

## When Escalation Happens

The **Human Escalation Agent** (`agents/escalation_agent.py`) creates a `ReviewTask` whenever:
- `confidence < CONFIDENCE_ESCALATION_THRESHOLD` (hard escalation — answer withheld), or
- The Evaluator Agent flags an explicit contradiction between retrieved sources, or
- A user submits `thumbs_down` feedback on a previously auto-answered response.

## Review Task Lifecycle

```
pending → in_review → resolved
```

- **pending** — visible in the Review Dashboard queue, sorted by priority (hard escalations first) then age.
- **in_review** — a reviewer has claimed the task (`POST /api/v1/review/{id}/claim`).
- **resolved** — reviewer submitted one of three outcomes:
  - `approve` — the AI's answer was correct; released to the user as-is.
  - `edit` — reviewer supplies a corrected answer; this is what's released, and the correction feeds the Knowledge Update Agent.
  - `reject` — the AI's answer was withheld entirely; reviewer may leave a note explaining why (e.g., "no source supports this").

## API Surface

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/review?status=pending` | List queued review tasks |
| `POST /api/v1/review/{id}/claim` | Reviewer claims a task |
| `POST /api/v1/review/{id}/resolve` | Submit `approve` / `edit` / `reject` with optional corrected content |

## Why This Matters

Confidence scores are a heuristic, not a guarantee. Routing uncertain answers to a human — rather than shipping a plausible-sounding hallucination — is the difference between a demo chatbot and a system an enterprise can actually trust with its knowledge base. Every reviewer decision is captured as a `FeedbackEvent`, which is the raw material the [context learning engine](context-learning-engine.md) uses to make the system smarter on the next similar question.
