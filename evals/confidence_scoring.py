"""Composite confidence scoring used by the Evaluator Agent.

confidence = 0.30 * retrieval_quality
           + 0.20 * source_relevance
           + 0.30 * self_check_score
           + 0.20 * historical_feedback_score

Each LLM-judged signal (source_relevance, self_check_score) degrades to a
deterministic lexical heuristic when no real chat client is configured, so
the whole scorer runs offline. See evaluation-framework.md for details.
"""
import re

WEIGHTS = {
    "retrieval_quality": 0.30,
    "source_relevance": 0.20,
    "self_check_score": 0.30,
    "historical_feedback_score": 0.20,
}


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _extract_float(text: str, default: float) -> float:
    match = re.search(r"(\d*\.?\d+)", text)
    if not match:
        return default
    try:
        value = float(match.group(1))
    except ValueError:
        return default
    return max(0.0, min(1.0, value))


def retrieval_quality(chunks: list[dict]) -> float:
    if not chunks:
        return 0.0
    similarities = [max(0.0, min(1.0, c["similarity"])) for c in chunks]
    return sum(similarities) / len(similarities)


def source_relevance(question: str, chunks: list[dict], chat_client=None) -> float:
    if not chunks:
        return 0.0

    if chat_client is not None:
        snippets = "\n".join(f"[{i + 1}] {c['content'][:500]}" for i, c in enumerate(chunks))
        prompt = (
            f"Question: {question}\n\nSnippets:\n{snippets}\n\n"
            "On average, how relevant are these snippets to answering the question? "
            "Respond with ONLY a single number between 0 and 1."
        )
        try:
            response = chat_client.complete(
                "You are a strict relevance grader. Respond with only a number.", prompt, temperature=0.0
            )
            return _extract_float(response, default=0.5)
        except Exception:  # noqa: BLE001 - fall back to heuristic on any API error
            pass

    question_tokens = _tokenize(question)
    if not question_tokens:
        return 0.5
    scores = []
    for chunk in chunks:
        chunk_tokens = _tokenize(chunk["content"])
        if not chunk_tokens:
            scores.append(0.0)
            continue
        overlap = len(question_tokens & chunk_tokens) / len(question_tokens)
        scores.append(min(1.0, overlap))
    return sum(scores) / len(scores)


def self_check_score(answer: str, chunks: list[dict], chat_client=None) -> float:
    if not answer:
        return 0.0

    context = "\n".join(f"[{i + 1}] {c['content'][:500]}" for i, c in enumerate(chunks))

    if chat_client is not None:
        prompt = (
            f"Context:\n{context}\n\nAnswer to check:\n{answer}\n\n"
            "What fraction of the claims in the answer are directly supported by the context? "
            "Respond with ONLY a single number between 0 (mostly unsupported) and 1 (fully supported)."
        )
        try:
            response = chat_client.complete(
                "You are a strict faithfulness grader. Respond with only a number.", prompt, temperature=0.0
            )
            return _extract_float(response, default=0.6)
        except Exception:  # noqa: BLE001 - fall back to heuristic on any API error
            pass

    context_tokens: set[str] = set()
    for chunk in chunks:
        context_tokens |= _tokenize(chunk["content"])
    significant_answer_tokens = {t for t in _tokenize(answer) if len(t) > 4}
    if not significant_answer_tokens:
        return 0.7
    supported = len(significant_answer_tokens & context_tokens)
    return min(1.0, supported / len(significant_answer_tokens))


def historical_feedback_score(chunk_ids: list[str], db=None) -> float:
    """Acceptance rate of past answers whose citations overlap with the
    given chunk ids. Returns a neutral 0.5 prior when there's no history."""
    if not chunk_ids or db is None:
        return 0.5

    from app.models.conversation import Answer
    from app.models.enums import FeedbackKind
    from app.models.feedback import FeedbackEvent

    positive_kinds = {FeedbackKind.thumbs_up, FeedbackKind.reviewer_approve}
    negative_kinds = {FeedbackKind.thumbs_down, FeedbackKind.reviewer_reject}
    chunk_id_set = set(chunk_ids)

    positive = 0
    negative = 0
    events = db.query(FeedbackEvent).all()
    for event in events:
        answer = db.get(Answer, event.answer_id)
        if answer is None:
            continue
        cited_ids = {c.get("chunk_id") for c in (answer.citations_json or [])}
        if not (cited_ids & chunk_id_set):
            continue
        if event.kind in positive_kinds:
            positive += 1
        elif event.kind in negative_kinds:
            negative += 1

    total = positive + negative
    if total == 0:
        return 0.5
    return positive / total


def score_answer(
    question: str,
    answer_content: str,
    chunks: list[dict],
    chat_client=None,
    db=None,
) -> dict:
    rq = retrieval_quality(chunks)
    sr = source_relevance(question, chunks, chat_client)
    sc = self_check_score(answer_content, chunks, chat_client)
    hf = historical_feedback_score([c["chunk_id"] for c in chunks], db)

    confidence = (
        WEIGHTS["retrieval_quality"] * rq
        + WEIGHTS["source_relevance"] * sr
        + WEIGHTS["self_check_score"] * sc
        + WEIGHTS["historical_feedback_score"] * hf
    )
    confidence = max(0.0, min(1.0, confidence))

    return {
        "retrieval_quality": round(rq, 4),
        "source_relevance": round(sr, 4),
        "self_check_score": round(sc, 4),
        "historical_feedback_score": round(hf, 4),
        "confidence": round(confidence, 4),
    }
