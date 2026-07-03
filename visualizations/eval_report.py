"""Renders the ContextPilot AI model evaluation report as a static figure:
aggregate RAGAS-style metrics (faithfulness, answer relevance, context
precision/recall, confidence) plus the per-question confidence distribution
against the configured escalation/auto-answer thresholds.

Usage (from repo root, with `pip install -r visualizations/requirements.txt`
and `pip install -r backend/requirements.txt` so evals.run_eval is available):

    # Render the most recent evals/reports/*.json report
    python -m visualizations.eval_report

    # Render a specific report file
    python -m visualizations.eval_report --report evals/reports/report_20260703T120000.json

    # No report yet? Preview the chart design with representative demo data
    python -m visualizations.eval_report --demo

Output: visualizations/outputs/eval_report.png
"""
import argparse
import glob
import json
import os
import sys

import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualizations.style import CHROME, STATUS, apply_style, strip_spines  # noqa: E402

METRIC_LABELS = {
    "mean_faithfulness": "Faithfulness",
    "mean_answer_relevance": "Answer relevance",
    "mean_context_precision": "Context precision",
    "mean_context_recall": "Context recall",
    "mean_confidence": "Mean confidence",
}

DEMO_REPORT = {
    "dataset_path": "evals/test_cases/sample_eval_set.jsonl",
    "aggregate": {
        "mean_faithfulness": 0.81,
        "mean_answer_relevance": 0.74,
        "mean_context_precision": 0.68,
        "mean_context_recall": 0.71,
        "mean_confidence": 0.70,
        "num_questions": 12,
    },
    "per_question": [
        {"question": f"q{i}", "confidence": c}
        for i, c in enumerate(
            [0.91, 0.87, 0.83, 0.79, 0.76, 0.74, 0.69, 0.65, 0.61, 0.58, 0.52, 0.44]
        )
    ],
}


def find_latest_report(report_dir: str) -> str | None:
    candidates = sorted(glob.glob(os.path.join(report_dir, "report_*.json")))
    return candidates[-1] if candidates else None


def load_report(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def render(report: dict, output_path: str, escalation_threshold: float, auto_answer_threshold: float) -> None:
    apply_style()
    fig, (ax_bars, ax_hist) = plt.subplots(1, 2, figsize=(11, 4.6), width_ratios=[1, 1.1])
    fig.suptitle("ContextPilot AI — Model Evaluation Report", fontsize=15, fontweight="bold", color=CHROME["ink_primary"])
    subtitle = f"dataset: {report.get('dataset_path', 'unknown')} · n={report['aggregate'].get('num_questions', '?')} questions"
    fig.text(0.5, 0.90, subtitle, ha="center", fontsize=9.5, color=CHROME["ink_muted"])

    # --- Panel 1: aggregate metrics, single hue (pure magnitude, 0-1 scale) ---
    labels = [METRIC_LABELS[k] for k in METRIC_LABELS if k in report["aggregate"]]
    values = [report["aggregate"][k] for k in METRIC_LABELS if k in report["aggregate"]]
    y_pos = range(len(labels))

    bars = ax_bars.barh(y_pos, values, height=0.55, color="#2a78d6", zorder=3)
    for bar, value in zip(bars, values):
        ax_bars.text(
            min(value + 0.02, 0.97), bar.get_y() + bar.get_height() / 2, f"{value:.2f}",
            va="center", ha="left", fontsize=9.5, color=CHROME["ink_primary"], fontweight="bold",
        )
    ax_bars.set_yticks(list(y_pos), labels)
    ax_bars.invert_yaxis()
    ax_bars.set_xlim(0, 1.08)
    ax_bars.set_xlabel("score (0–1)")
    ax_bars.set_title("Aggregate metrics", loc="left")
    strip_spines(ax_bars, keep=("bottom",))
    ax_bars.grid(axis="y", visible=False)
    ax_bars.grid(axis="x", visible=True)

    # --- Panel 2: confidence distribution vs. decision thresholds -------------
    confidences = [q["confidence"] for q in report.get("per_question", [])]
    counts = []
    if confidences:
        counts, _, _ = ax_hist.hist(
            confidences, bins=10, range=(0, 1), color="#2a78d6", alpha=0.85,
            edgecolor=CHROME["surface"], linewidth=1.2, zorder=3,
        )
    max_count = max(counts) if len(counts) else 1
    y_top = max_count * 1.35  # headroom so threshold labels never collide with the title
    ax_hist.set_ylim(0, y_top)
    ax_hist.axvline(escalation_threshold, color=STATUS["critical"], linewidth=2, linestyle="--", zorder=4)
    ax_hist.axvline(auto_answer_threshold, color=STATUS["good"], linewidth=2, linestyle="--", zorder=4)
    label_y = max_count * 1.12
    ax_hist.text(
        escalation_threshold - 0.02, label_y, f"escalate < {escalation_threshold:.2f}",
        ha="right", va="bottom", fontsize=8.5, color=STATUS["critical"], fontweight="bold",
    )
    ax_hist.text(
        auto_answer_threshold + 0.02, label_y, f"auto-answer ≥ {auto_answer_threshold:.2f}",
        ha="left", va="bottom", fontsize=8.5, color=STATUS["good"], fontweight="bold",
    )
    ax_hist.set_xlim(0, 1)
    ax_hist.set_xlabel("confidence score")
    ax_hist.set_ylabel("questions")
    ax_hist.set_title("Confidence distribution", loc="left", pad=14)
    strip_spines(ax_hist, keep=("bottom", "left"))

    fig.tight_layout(rect=[0, 0, 1, 0.87])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=180)
    print(f"Wrote {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the ContextPilot AI evaluation report.")
    parser.add_argument("--report", default=None, help="Path to a specific evals/reports/*.json file")
    parser.add_argument("--report-dir", default="evals/reports")
    parser.add_argument("--output", default="visualizations/outputs/eval_report.png")
    parser.add_argument("--escalation-threshold", type=float, default=0.62)
    parser.add_argument("--auto-answer-threshold", type=float, default=0.80)
    parser.add_argument("--demo", action="store_true", help="Use representative demo data instead of a real report")
    args = parser.parse_args()

    if args.demo:
        report = DEMO_REPORT
    else:
        report_path = args.report or find_latest_report(args.report_dir)
        if report_path is None:
            print(
                f"No eval report found in {args.report_dir}/. Run "
                "`python -m evals.run_eval --dataset evals/test_cases/sample_eval_set.jsonl` first, "
                "or pass --demo to preview the chart with representative data.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        report = load_report(report_path)

    render(report, args.output, args.escalation_threshold, args.auto_answer_threshold)


if __name__ == "__main__":
    main()
