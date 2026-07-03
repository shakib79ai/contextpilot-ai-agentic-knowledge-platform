# Visualizations

Static matplotlib figures for the model evaluation report, confidence-threshold
optimization, and the multi-agent workflow architecture — useful for the repo
README, a slide deck, or a write-up.

These scripts are deliberately decoupled from the backend: they only need
`matplotlib`/`numpy`, not the full agent stack, so they run in a lightweight
venv without Docker or Postgres.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   macOS/Linux: source .venv/bin/activate
pip install -r visualizations/requirements.txt
```

Run all commands from the repo root.

## 1. Model evaluation report

Renders aggregate RAGAS-style metrics plus the per-question confidence
distribution against the configured decision thresholds.

```bash
# Uses the most recent evals/reports/*.json (generate one first with:
#   pip install -r backend/requirements.txt
#   python -m evals.run_eval --dataset evals/test_cases/sample_eval_set.jsonl )
python -m visualizations.eval_report

# No report yet? Preview the chart with representative demo data:
python -m visualizations.eval_report --demo
```

→ `visualizations/outputs/eval_report.png`

## 2. Confidence-threshold optimization

Sweeps `CONFIDENCE_ESCALATION_THRESHOLD` and shows what share of answers
would be auto-answered / flagged low-confidence / escalated at each value —
the chart to look at when deciding where to set the thresholds in `.env`.

```bash
python -m visualizations.threshold_optimization
python -m visualizations.threshold_optimization --demo
```

→ `visualizations/outputs/threshold_optimization.png`

## 3. Workflow architecture diagram

A static schematic of the query-time agent graph, the human-in-the-loop
review flow, and the ingestion / context-learning feedback loop.

```bash
python -m visualizations.architecture_diagram
```

→ `visualizations/outputs/architecture_diagram.png`

## Design notes

Colors follow a single fixed palette across all three figures (see
`style.py`): a categorical theme for agent/component identity, one hue
(blue) for pure magnitude bars, and a reserved status palette
(green/yellow/red) for good/warning/critical outcomes — so "auto-answered",
"low-confidence", and "escalated" always mean the same color everywhere,
matching the frontend's badge colors in `frontend/app/globals.css`.
