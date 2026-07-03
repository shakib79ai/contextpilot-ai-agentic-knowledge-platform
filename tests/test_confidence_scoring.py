from evals.confidence_scoring import historical_feedback_score, retrieval_quality, score_answer, self_check_score, source_relevance


CHUNKS = [
    {"chunk_id": "c1", "content": "ContextPilot AI escalates low-confidence answers to a human reviewer.", "similarity": 0.91, "source": "document"},
    {"chunk_id": "c2", "content": "The evaluator agent scores retrieval quality, relevance, and self-check.", "similarity": 0.77, "source": "document"},
]


def test_retrieval_quality_averages_similarities():
    assert retrieval_quality(CHUNKS) == (0.91 + 0.77) / 2
    assert retrieval_quality([]) == 0.0


def test_source_relevance_heuristic_in_range():
    score = source_relevance("How does ContextPilot AI escalate answers?", CHUNKS)
    assert 0.0 <= score <= 1.0


def test_self_check_score_rewards_grounded_answers():
    grounded = "ContextPilot AI escalates low-confidence answers to a human reviewer."
    ungrounded = "Bananas are a great source of potassium and grow on trees."
    grounded_score = self_check_score(grounded, CHUNKS)
    ungrounded_score = self_check_score(ungrounded, CHUNKS)
    assert grounded_score > ungrounded_score


def test_historical_feedback_score_defaults_neutral_without_db():
    assert historical_feedback_score(["c1", "c2"], db=None) == 0.5
    assert historical_feedback_score([], db=None) == 0.5


def test_score_answer_combines_signals_into_bounded_confidence():
    breakdown = score_answer(
        question="How does ContextPilot AI escalate answers?",
        answer_content="ContextPilot AI escalates low-confidence answers to a human reviewer.",
        chunks=CHUNKS,
    )
    assert 0.0 <= breakdown["confidence"] <= 1.0
    assert set(breakdown.keys()) == {
        "retrieval_quality", "source_relevance", "self_check_score", "historical_feedback_score", "confidence",
    }
