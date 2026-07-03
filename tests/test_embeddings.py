from rag_pipeline.embeddings import LocalHashEmbeddingClient, is_placeholder_key


def test_placeholder_key_detection():
    assert is_placeholder_key("")
    assert is_placeholder_key("sk-REPLACE_WITH_YOUR_OPENAI_API_KEY")
    assert not is_placeholder_key("sk-live-abc123")


def test_local_hash_embedding_is_deterministic_and_normalized():
    client = LocalHashEmbeddingClient()
    v1 = client.embed_query("What is ContextPilot AI?")
    v2 = client.embed_query("What is ContextPilot AI?")
    assert v1 == v2
    assert len(v1) == client.dimension

    norm = sum(x * x for x in v1) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_local_hash_embedding_differs_for_different_text():
    client = LocalHashEmbeddingClient()
    v1 = client.embed_query("apples")
    v2 = client.embed_query("orbital mechanics")
    assert v1 != v2
