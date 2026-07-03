"""Similarity search + citation formatting, used by the Retriever Agent."""
from dataclasses import dataclass

from app.config import get_settings
from rag_pipeline.embeddings import get_embedding_client
from rag_pipeline.vector_store import get_vector_store


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str | None
    content: str
    similarity: float
    source: str
    metadata: dict


class Retriever:
    def __init__(self, settings=None):
        self._settings = settings or get_settings()
        self._embedding_client = get_embedding_client(self._settings)
        self._vector_store = get_vector_store(self._settings, dimension=self._embedding_client.dimension)

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_vector = self._embedding_client.embed_query(question)
        results = self._vector_store.search(query_vector, top_k=top_k)
        return [
            RetrievedChunk(
                chunk_id=r.id,
                document_id=r.metadata.get("document_id"),
                content=r.metadata.get("content", ""),
                similarity=r.score,
                source=r.metadata.get("source", "document"),
                metadata=r.metadata,
            )
            for r in results
        ]

    def index_correction(self, chunk_id: str, content: str, metadata: dict) -> None:
        """Used by the Context Learning Engine to upsert a human-verified
        correction as a first-class, higher-priority chunk."""
        vector = self._embedding_client.embed_query(content)
        self._vector_store.upsert(
            ids=[chunk_id],
            vectors=[vector],
            metadatas=[{**metadata, "content": content, "source": "human_correction"}],
        )
