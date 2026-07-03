# Evaluation & Confidence Framework

## Composite Confidence Score

`evals/confidence_scoring.py` computes a single `confidence ∈ [0, 1]` per answer:

```
confidence = 0.30 * retrieval_quality
            + 0.20 * source_relevance
            + 0.30 * self_check_score
            + 0.20 * historical_feedback_score
```

| Signal | How it's computed |
|---|---|
| **retrieval_quality** | Mean cosine similarity of the top-k retrieved chunks, normalized to [0,1] |
| **source_relevance** | LLM-as-judge: "Given this question and this chunk, rate relevance 0-1" (averaged, cached per chunk/question pair) |
| **self_check_score** | LLM asked to identify claims in its own answer unsupported by the retrieved context; score = 1 − (unsupported_claims / total_claims) |
| **historical_feedback_score** | Acceptance rate of past answers whose retrieved chunks overlap with this answer's chunks (defaults to 0.5 — neutral — when no history exists) |

Thresholds (configurable via `.env`):
- `CONFIDENCE_AUTO_ANSWER_THRESHOLD` (default `0.80`) — answer is shown to the user immediately.
- `CONFIDENCE_ESCALATION_THRESHOLD` (default `0.62`) — below this, the answer is withheld pending human review.
- Between the two thresholds, the answer is shown but flagged `low_confidence` and queued for low-priority async review.

## RAGAS-Style Batch Evaluation

`evals/ragas_eval.py` implements a lightweight, dependency-free approximation of the standard RAG metrics so the eval suite can run without a live RAGAS install:

- **Faithfulness** — fraction of answer sentences supported by retrieved context
- **Answer Relevance** — embedding similarity between the question and a reverse-generated question from the answer
- **Context Precision** — fraction of retrieved chunks actually used in the final answer
- **Context Recall** — fraction of the gold-answer's supporting facts present in the retrieved chunks (requires a labeled eval set)

## Eval Sets

`evals/test_cases/` holds JSONL eval sets in the form:

```json
{"question": "...", "gold_answer": "...", "gold_context_ids": ["chunk_123"]}
```

Run with:

```bash
python -m evals.run_eval --dataset evals/test_cases/sample_eval_set.jsonl
```

This produces a per-question and aggregate report (faithfulness, relevance, precision, recall, and mean confidence vs. gold correctness) written to `evals/reports/`.

## CI Gate

`.github/workflows/ci.yml` runs the eval suite against `evals/test_cases/sample_eval_set.jsonl` on every PR touching `agents/`, `rag_pipeline/`, or `evals/`, and fails the build if mean faithfulness drops below a configured regression threshold.

## Observability

When `LANGCHAIN_TRACING_V2=true` and `LANGSMITH_API_KEY` is set, every agent-graph run is traced end-to-end in LangSmith, including per-node latency, token usage, and the exact prompt/response pairs — critical for debugging low-confidence answers in production.
