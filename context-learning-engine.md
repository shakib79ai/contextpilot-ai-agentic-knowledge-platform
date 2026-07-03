# Context Learning Engine

Most RAG systems are static: the knowledge base only changes when someone manually re-uploads documents. ContextPilot AI's Context Learning Engine (`context_learning/`) closes the loop — feedback from real usage continuously improves future answers.

## What Gets Captured

Every `FeedbackEvent` (thumbs up/down, reviewer approve/edit/reject) is stored with a reference to:
- the original question and answer,
- the exact chunks that were retrieved and cited,
- the confidence score at the time, and
- the reviewer's correction, if any.

## How Feedback Becomes Context

`context_learning/learning_engine.py` runs periodically (via Celery beat, `tasks/learning.py`) and:

1. **Surfaces high-value corrections** — reviewer-edited answers where the correction diverges meaningfully from the original.
2. **Re-embeds corrections as first-class chunks** — stored with `metadata.source = "human_correction"` and a higher retrieval-priority weight, so future similar questions are more likely to retrieve the *corrected* fact rather than the original (possibly outdated) document chunk.
3. **Updates historical feedback scores** — the acceptance-rate signal used by the confidence scorer (see [evaluation-framework.md](evaluation-framework.md)) is recomputed per document/chunk cluster.
4. **Feeds the Knowledge Update Agent** — corrections that look like factual drift (not just phrasing preference) become `KnowledgeUpdate` proposals for a human to approve against the source document itself, rather than just living as a side-channel correction.

## Why Separate "Corrections" from "Source Documents"

Human corrections are treated as provisional, high-trust context — not silently merged into the original document — so that:
- provenance is always traceable (a cited correction clearly says "human-verified on {date}, superseding chunk {id}"),
- a reviewer can later approve/reject the correction being permanently merged into the source document via the Knowledge Update workflow, and
- the system never overwrites an enterprise's actual source-of-truth documents without an explicit human approval step.

## Decay & Re-validation

Corrections older than a configurable staleness window are re-surfaced to reviewers for re-confirmation, preventing the knowledge base from silently drifting on outdated "fixes" the same way it would on outdated source documents.
