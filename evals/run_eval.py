"""Batch evaluation runner.

Usage:
    python -m evals.run_eval --dataset evals/test_cases/sample_eval_set.jsonl
"""
import argparse
import json
import os
from datetime import datetime, timezone

from evals import ragas_eval
from evals.metrics import aggregate_report


def _load_dataset(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run_eval(dataset_path: str, report_dir: str = "evals/reports") -> dict:
    from agents.graph import run_query_graph

    dataset = _load_dataset(dataset_path)
    per_question = []

    for example in dataset:
        question = example["question"]
        state = run_query_graph(question, top_k=5, db=None)

        answer = state.get("answer_content", "")
        chunks = state.get("retrieved_chunks", [])

        per_question.append(
            {
                "question": question,
                "answer": answer,
                "confidence": state.get("confidence", 0.0),
                "faithfulness": ragas_eval.faithfulness(answer, chunks),
                "answer_relevance": ragas_eval.answer_relevance(question, answer),
                "context_precision": ragas_eval.context_precision(answer, chunks),
                "context_recall": ragas_eval.context_recall(chunks, example.get("gold_context_ids", [])),
            }
        )

    report = {
        "dataset_path": dataset_path,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aggregate": aggregate_report(per_question),
        "per_question": per_question,
    }

    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    report["report_path"] = report_path
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ContextPilot AI evaluation suite.")
    parser.add_argument("--dataset", default="evals/test_cases/sample_eval_set.jsonl")
    parser.add_argument("--report-dir", default="evals/reports")
    args = parser.parse_args()

    report = run_eval(args.dataset, args.report_dir)
    print(json.dumps(report["aggregate"], indent=2))
    print(f"Full report written to {report['report_path']}")


if __name__ == "__main__":
    main()
