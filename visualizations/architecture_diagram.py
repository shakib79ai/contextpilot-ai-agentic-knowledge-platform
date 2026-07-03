"""Static workflow/architecture diagram of the ContextPilot AI multi-agent
pipeline: query-time agent graph, human-in-the-loop review, and the
document-ingestion / context-learning feedback loop.

Usage:
    python -m visualizations.architecture_diagram

Output: visualizations/outputs/architecture_diagram.png
"""
import os
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualizations.style import CATEGORICAL, CHROME, STATUS, apply_style  # noqa: E402

BOX_W, BOX_H = 2.0, 0.95


def add_box(ax, x, y, text, face, text_color="#ffffff", style="round,pad=0.02,rounding_size=0.12", width=BOX_W, height=BOX_H, fontsize=9.3, edge=None):
    """x, y is the box CENTER. Returns the center point for arrow anchoring."""
    box = FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height,
        boxstyle=style, facecolor=face, edgecolor=edge or face, linewidth=1.2, zorder=3,
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, color=text_color, fontweight="bold", zorder=4, wrap=True)
    return (x, y)


def add_arrow(ax, start, end, color, rad=0.0, style="-|>", lw=1.6, ls="solid"):
    arrow = FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=14, color=color, linewidth=lw,
        linestyle=ls, connectionstyle=f"arc3,rad={rad}", zorder=2, shrinkA=6, shrinkB=6,
    )
    ax.add_patch(arrow)


def add_label(ax, x, y, text, color=None):
    ax.text(x, y, text, ha="center", va="center", fontsize=8, color=color or CHROME["ink_muted"], style="italic", zorder=5,
             bbox=dict(facecolor=CHROME["page"], edgecolor="none", pad=1.0))


def render(output_path: str) -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(-0.5, 15.5)
    ax.set_ylim(-0.5, 10.8)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.suptitle("ContextPilot AI — Multi-Agent Workflow Architecture", fontsize=16, fontweight="bold", color=CHROME["ink_primary"], y=0.98)

    # --- Lane backgrounds ----------------------------------------------------
    lane_specs = [
        (8.9, "A · Query-time agent graph (LangGraph)"),
        (5.15, "B · Human-in-the-loop review & knowledge update"),
        (1.4, "C · Document ingestion & context learning (async, Celery)"),
    ]
    for cy, label in lane_specs:
        ax.add_patch(plt.Rectangle((-0.3, cy - 1.55), 15.6, 3.1, facecolor=CHROME["surface"], edgecolor=CHROME["gridline"], zorder=1))
        ax.text(-0.2, cy + 1.35, label, ha="left", va="top", fontsize=10, color=CHROME["ink_secondary"], fontweight="bold", zorder=2)

    # --- Lane A: query-time pipeline ------------------------------------------
    y_a = 8.9
    p_user = add_box(ax, 1.0, y_a, "User\nquestion", CHROME["ink_muted"])
    p_api = add_box(ax, 3.4, y_a, "API Gateway\n(FastAPI)", CATEGORICAL["blue"])
    p_retriever = add_box(ax, 5.8, y_a, "Retriever\nAgent", CATEGORICAL["aqua"])
    p_answer = add_box(ax, 8.2, y_a, "Answer\nAgent", CATEGORICAL["violet"])
    p_evaluator = add_box(ax, 10.6, y_a, "Evaluator\nAgent", CATEGORICAL["orange"])
    p_decision = add_box(ax, 13.0, y_a, "Confidence\ndecision", CHROME["ink_secondary"])

    for a, b in [(p_user, p_api), (p_api, p_retriever), (p_retriever, p_answer), (p_answer, p_evaluator), (p_evaluator, p_decision)]:
        add_arrow(ax, (a[0] + BOX_W / 2, a[1]), (b[0] - BOX_W / 2, b[1]), CHROME["ink_muted"])

    # decision -> auto-answered (back to user), good/green
    p_auto = add_box(ax, 13.0, y_a - 2.1, "Auto-answered\n(≥ 0.80)", STATUS["good"], width=2.2)
    add_arrow(ax, (p_decision[0], p_decision[1] - BOX_H / 2), (p_auto[0], p_auto[1] + BOX_H / 2), STATUS["good"])
    add_arrow(ax, (p_auto[0] - BOX_W / 2 - 0.2, p_auto[1]), (p_user[0], p_user[1] - BOX_H / 2 - 0.15), STATUS["good"], rad=0.25, ls="dashed")

    # --- Lane B: human review + knowledge update -------------------------------
    y_b = 5.15
    p_escalate = add_box(ax, 13.0, y_b, "Human\nEscalation Agent", STATUS["critical"])
    add_arrow(ax, (p_decision[0], p_decision[1] - BOX_H / 2 - 0.6), (p_escalate[0], p_escalate[1] + BOX_H / 2), STATUS["critical"], rad=-0.15)
    add_label(ax, 13.9, y_a - 1.0, "< 0.62 → escalate\n0.62–0.80 → flag + audit", STATUS["critical"])

    p_queue = add_box(ax, 10.4, y_b, "Review Queue\n(ReviewTask)", CATEGORICAL["red"])
    p_reviewer = add_box(ax, 7.8, y_b, "Human\nReviewer", CATEGORICAL["yellow"], text_color="#0b0b0b")
    p_kb_agent = add_box(ax, 5.2, y_b, "Knowledge Update\nAgent", CATEGORICAL["green"])
    p_learning = add_box(ax, 2.6, y_b, "Context Learning\nEngine", CATEGORICAL["blue"])

    add_arrow(ax, (p_escalate[0] - BOX_W / 2, p_escalate[1]), (p_queue[0] + BOX_W / 2, p_queue[1]), CHROME["ink_muted"])
    add_arrow(ax, (p_queue[0] - BOX_W / 2, p_queue[1]), (p_reviewer[0] + BOX_W / 2, p_reviewer[1]), CHROME["ink_muted"])

    p_terminal = add_box(ax, 7.8, y_b - 2.05, "approve / reject\n→ release or withhold", CHROME["ink_muted"], width=2.3, fontsize=8.6)
    add_arrow(ax, (p_reviewer[0], p_reviewer[1] - BOX_H / 2), (p_terminal[0], p_terminal[1] + BOX_H / 2), CHROME["ink_muted"])

    add_arrow(ax, (p_reviewer[0] - BOX_W / 2, p_reviewer[1]), (p_kb_agent[0] + BOX_W / 2, p_kb_agent[1]), CATEGORICAL["green"])
    add_label(ax, 6.5, y_b + 0.75, "decision: edit", CATEGORICAL["green"])
    add_arrow(ax, (p_kb_agent[0] - BOX_W / 2, p_kb_agent[1]), (p_learning[0] + BOX_W / 2, p_learning[1]), CATEGORICAL["blue"])

    # --- Lane C: ingestion + vector store ---------------------------------------
    y_c = 1.4
    p_upload = add_box(ax, 1.0, y_c, "Document\nUpload", CATEGORICAL["blue"])
    p_celery = add_box(ax, 3.4, y_c, "Celery Worker\nchunk → embed", CATEGORICAL["aqua"])
    p_vectorstore = add_box(ax, 5.8, y_c, "Vector Store\n(FAISS)", CATEGORICAL["magenta"])

    add_arrow(ax, (p_upload[0] + BOX_W / 2, p_upload[1]), (p_celery[0] - BOX_W / 2, p_celery[1]), CHROME["ink_muted"])
    add_arrow(ax, (p_celery[0] + BOX_W / 2, p_celery[1]), (p_vectorstore[0] - BOX_W / 2, p_vectorstore[1]), CHROME["ink_muted"])

    # vector store <-> retriever (RAG lookup), straight vertical
    add_arrow(ax, (p_vectorstore[0], p_vectorstore[1] + BOX_H / 2), (p_retriever[0], p_retriever[1] - BOX_H / 2), CATEGORICAL["aqua"], rad=0.0)
    add_label(ax, p_vectorstore[0] + 0.05, 7.02, "similarity\nsearch", CATEGORICAL["aqua"])

    # context learning -> vector store (re-index correction), curved feedback loop
    add_arrow(ax, (p_learning[0] - 0.3, p_learning[1] - BOX_H / 2), (p_vectorstore[0] - 0.6, p_vectorstore[1] + BOX_H / 2), CATEGORICAL["blue"], rad=0.3, ls="dashed")
    add_label(ax, 1.6, 3.3, "re-index as\nhigh-trust correction", CATEGORICAL["blue"])

    fig.tight_layout(rect=[0, 0, 1, 0.955])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=170)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    render(os.path.join("visualizations", "outputs", "architecture_diagram.png"))
