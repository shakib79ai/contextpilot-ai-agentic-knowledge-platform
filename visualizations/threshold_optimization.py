"""Confidence-threshold optimization sweep.

Answers a concrete tuning question: as CONFIDENCE_ESCALATION_THRESHOLD moves,
what share of answers get auto-answered vs. flagged low-confidence vs. fully
escalated to a human reviewer? Renders a stacked-area sweep over a
distribution of confidence scores (from a real eval report, or representative
demo data), with the currently configured threshold marked.

Usage:
    python -m visualizations.threshold_optimization
    python -m visualizations.threshold_optimization --report evals/reports/report_20260703T120000.json
    python -m visualizations.threshold_optimization --demo

Output: visualizations/outputs/threshold_optimization.png
"""
import argparse
import glob
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualizations.style import CHROME, STATUS, apply_style, strip_spines  # noqa: E402

# Representative confidence scores across a plausible eval run — used only
# when no real eval report is available (see --demo).
DEMO_CONFIDENCES = [
    0.93, 0.90, 0.88, 0.85, 0.83, 0.81, 0.78, 0.76, 0.74, 0.72,
    0.70, 0.68, 0.66, 0.64, 0.62, 0.60, 0.58, 0.55, 0.52, 0.49,
    0.46, 0.43, 0.40, 0.36, 0.32, 0.28, 0.24, 0.20, 0.15, 0.10,
]


def find_latest_report(report_dir: str) -> str | None:
    candidates = sorted(glob.glob(os.path.join(report_dir, "report_*.json")))
    return candidates[-1] if candidates else None


def load_confidences(report_path: str | None) -> list[float]:
    if report_path is None:
        return DEMO_CONFIDENCES
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)
    return [q["confidence"] for q in report.get("per_question", [])]


def sweep(confidences: np.ndarray, auto_answer_threshold: float, num_points: int = 60):
    thresholds = np.linspace(0.0, auto_answer_threshold, num_points)
    escalated_pct, low_confidence_pct, auto_answered_pct = [], [], []
    n = len(confidences)
    for t in thresholds:
        escalated = np.sum(confidences < t) / n * 100
        auto = np.sum(confidences >= auto_answer_threshold) / n * 100
        low = 100 - escalated - auto
        escalated_pct.append(escalated)
        low_confidence_pct.append(low)
        auto_answered_pct.append(auto)
    return thresholds, np.array(escalated_pct), np.array(low_confidence_pct), np.array(auto_answered_pct)


def render(confidences: list[float], output_path: str, auto_answer_threshold: float, current_threshold: float) -> None:
    apply_style()
    confidences = np.array(confidences)
    thresholds, escalated_pct, low_pct, auto_pct = sweep(confidences, auto_answer_threshold)

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.suptitle("ContextPilot AI — Escalation Threshold Optimization", fontsize=14.5, fontweight="bold", color=CHROME["ink_primary"])
    fig.text(
        0.5, 0.905, f"share of answers by outcome as CONFIDENCE_ESCALATION_THRESHOLD moves (auto-answer fixed at {auto_answer_threshold:.2f})",
        ha="center", fontsize=9.5, color=CHROME["ink_muted"],
    )

    ax.stackplot(
        thresholds,
        escalated_pct, low_pct, auto_pct,
        colors=[STATUS["critical"], STATUS["warning"], STATUS["good"]],
        labels=["Escalated (withheld, sent to reviewer)", "Low-confidence (shown, flagged for audit)", "Auto-answered"],
        alpha=0.9,
        zorder=3,
    )

    ax.axvline(current_threshold, color=CHROME["ink_primary"], linewidth=1.6, linestyle="--", zorder=4)
    ax.text(
        current_threshold, 103, f"current: {current_threshold:.2f}",
        ha="center", va="bottom", fontsize=9, color=CHROME["ink_primary"], fontweight="bold",
    )

    ax.set_xlim(0, auto_answer_threshold)
    ax.set_ylim(0, 100)
    ax.set_xlabel("CONFIDENCE_ESCALATION_THRESHOLD")
    ax.set_ylabel("% of answers")
    strip_spines(ax, keep=("bottom", "left"))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, frameon=False)

    fig.tight_layout(rect=[0, 0.02, 1, 0.87])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=180)
    print(f"Wrote {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the confidence-threshold optimization sweep.")
    parser.add_argument("--report", default=None)
    parser.add_argument("--report-dir", default="evals/reports")
    parser.add_argument("--output", default="visualizations/outputs/threshold_optimization.png")
    parser.add_argument("--auto-answer-threshold", type=float, default=0.80)
    parser.add_argument("--current-threshold", type=float, default=0.62)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    report_path = None if args.demo else (args.report or find_latest_report(args.report_dir))
    if report_path is None and not args.demo:
        print(
            f"No eval report found in {args.report_dir}/ — using representative demo data. "
            "Run `python -m evals.run_eval` for a report based on real answers, or pass --demo explicitly.",
            file=sys.stderr,
        )

    confidences = load_confidences(report_path)
    render(confidences, args.output, args.auto_answer_threshold, args.current_threshold)


if __name__ == "__main__":
    main()
