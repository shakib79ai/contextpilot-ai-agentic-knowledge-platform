"""Small aggregation helpers shared by the eval runner."""


def mean(values: list[float]) -> float:
    values = [v for v in values if v is not None]
    if not values:
        return 0.0
    return sum(values) / len(values)


def aggregate_report(per_question: list[dict]) -> dict:
    keys = ["faithfulness", "answer_relevance", "context_precision", "context_recall", "confidence"]
    return {f"mean_{key}": round(mean([q.get(key) for q in per_question]), 4) for key in keys} | {
        "num_questions": len(per_question)
    }
