from rag_pipeline.vector_store import FAISSVectorStore


def test_faiss_upsert_and_search_roundtrip(tmp_path):
    store = FAISSVectorStore(str(tmp_path / "vs"), dimension=8)

    store.upsert(
        ids=["a", "b"],
        vectors=[[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]],
        metadatas=[{"content": "vector a"}, {"content": "vector b"}],
    )

    results = store.search([1, 0, 0, 0, 0, 0, 0, 0], top_k=1)
    assert len(results) == 1
    assert results[0].id == "a"
    assert results[0].metadata["content"] == "vector a"


def test_faiss_persists_across_reload(tmp_path):
    directory = str(tmp_path / "vs")
    store1 = FAISSVectorStore(directory, dimension=4)
    store1.upsert(ids=["x"], vectors=[[1, 1, 1, 1]], metadatas=[{"content": "persisted"}])

    store2 = FAISSVectorStore(directory, dimension=4)
    results = store2.search([1, 1, 1, 1], top_k=1)
    assert len(results) == 1
    assert results[0].metadata["content"] == "persisted"


def test_faiss_delete_removes_vector(tmp_path):
    store = FAISSVectorStore(str(tmp_path / "vs"), dimension=4)
    store.upsert(ids=["x"], vectors=[[1, 0, 0, 0]], metadatas=[{"content": "to remove"}])
    store.delete(["x"])
    assert store.search([1, 0, 0, 0], top_k=5) == []
