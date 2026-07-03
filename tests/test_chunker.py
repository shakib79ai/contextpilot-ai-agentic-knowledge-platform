from rag_pipeline.chunker import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_returns_single_chunk():
    chunks = chunk_text("ContextPilot AI answers enterprise questions with citations.")
    assert len(chunks) == 1
    assert chunks[0].index == 0


def test_long_text_is_split_with_overlap():
    text = " ".join(f"word{i}" for i in range(2000))
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    # every chunk index should be sequential starting at 0
    assert [c.index for c in chunks] == list(range(len(chunks)))
    # reconstructing chunks should cover the whole document (allowing overlap)
    covered_words = set()
    for c in chunks:
        covered_words.update(c.content.split())
    assert "word0" in covered_words
    assert "word1999" in covered_words
