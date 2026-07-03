"""Lightweight, dependency-free approximations of the standard RAGAS metrics
so the eval suite can run offline/in CI without a live RAGAS + LLM-judge
install. See evaluation-framework.md for the metric definitions."""
import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def faithfulness(answer: str, retrieved_chunks: list[dict]) -> float:
    """Fraction of answer sentences with meaningful lexical overlap with the
    retrieved context (a proxy for "supported by context")."""
    sentences = [s for s in _SENTENCE_SPLIT.split(answer.strip()) if s.strip()]
    if not sentences:
        return 0.0

    context_tokens: set[str] = set()
    for chunk in retrieved_chunks:
        context_tokens |= _tokenize(chunk.get("content", ""))

    supported = 0
    for sentence in sentences:
        sentence_tokens = {t for t in _tokenize(sentence) if len(t) > 3}
        if not sentence_tokens:
            supported += 1
            continue
        overlap = len(sentence_tokens & context_tokens) / len(sentence_tokens)
        if overlap >= 0.4:
            supported += 1
    return supported / len(sentences)


def answer_relevance(question: str, answer: str) -> float:
    """Token-overlap proxy for how directly the answer addresses the
    question (real RAGAS reverse-generates a question from the answer and
    embeds it; we approximate with lexical overlap to stay dependency-free)."""
    q_tokens = {t for t in _tokenize(question) if len(t) > 2}
    a_tokens = _tokenize(answer)
    if not q_tokens:
        return 0.5
    overlap = len(q_tokens & a_tokens) / len(q_tokens)
    return min(1.0, overlap)


def context_precision(answer: str, retrieved_chunks: list[dict]) -> float:
    """Fraction of retrieved chunks that were actually drawn upon in the
    final answer."""
    if not retrieved_chunks:
        return 0.0
    answer_tokens = {t for t in _tokenize(answer) if len(t) > 3}
    used = 0
    for chunk in retrieved_chunks:
        chunk_tokens = {t for t in _tokenize(chunk.get("content", "")) if len(t) > 3}
        if chunk_tokens and len(chunk_tokens & answer_tokens) / len(chunk_tokens) >= 0.15:
            used += 1
    return used / len(retrieved_chunks)


def context_recall(retrieved_chunks: list[dict], gold_context_ids: list[str]) -> float | None:
    """Fraction of the gold-labeled supporting chunks that were retrieved.
    Returns None when the eval example has no gold context labels."""
    if not gold_context_ids:
        return None
    retrieved_ids = {c.get("chunk_id") for c in retrieved_chunks}
    hit = len(set(gold_context_ids) & retrieved_ids)
    return hit / len(gold_context_ids)
