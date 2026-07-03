from evals import ragas_eval

CHUNKS = [{"chunk_id": "c1", "content": "ContextPilot AI escalates low-confidence answers to a human reviewer."}]


def test_faithfulness_no_answer_is_zero():
    assert ragas_eval.faithfulness("", CHUNKS) == 0.0


def test_faithfulness_grounded_sentence_is_supported():
    score = ragas_eval.faithfulness("ContextPilot AI escalates low-confidence answers to a human reviewer.", CHUNKS)
    assert score == 1.0


def test_context_precision_empty_chunks_is_zero():
    assert ragas_eval.context_precision("some answer", []) == 0.0


def test_context_recall_none_when_no_gold_labels():
    assert ragas_eval.context_recall(CHUNKS, []) is None


def test_context_recall_computes_hit_rate():
    assert ragas_eval.context_recall(CHUNKS, ["c1", "c2"]) == 0.5
