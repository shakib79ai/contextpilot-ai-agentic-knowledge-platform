"""Vector store abstraction. FAISS is the default local backend; Pinecone and
Weaviate adapters are provided for managed/cloud deployments and are selected
purely via `VECTOR_STORE_PROVIDER` — agent and API code never depends on a
specific backend.
"""
from __future__ import annotations

import json
import os
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    id: str
    score: float
    metadata: dict = field(default_factory=dict)


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, ids: list[str], vectors: list[list[float]], metadatas: list[dict]) -> None: ...

    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]: ...

    @abstractmethod
    def delete(self, ids: list[str]) -> None: ...


class FAISSVectorStore(VectorStore):
    """Local, disk-persisted FAISS index using inner product over
    L2-normalized vectors (== cosine similarity)."""

    def __init__(self, directory: str, dimension: int):
        import faiss  # noqa: PLC0415 - optional heavy dependency, imported lazily
        import numpy as np  # noqa: PLC0415

        self._faiss = faiss
        self._np = np
        self._dimension = dimension
        self._directory = directory
        self._index_path = os.path.join(directory, "index.faiss")
        self._meta_path = os.path.join(directory, "meta.json")
        self._lock = threading.Lock()

        os.makedirs(directory, exist_ok=True)
        self._id_to_row: dict[str, int] = {}
        self._row_to_meta: dict[int, dict] = {}

        if os.path.exists(self._index_path) and os.path.exists(self._meta_path):
            self._index = faiss.read_index(self._index_path)
            with open(self._meta_path, encoding="utf-8") as f:
                saved = json.load(f)
            self._id_to_row = saved["id_to_row"]
            self._row_to_meta = {int(k): v for k, v in saved["row_to_meta"].items()}
        else:
            self._index = faiss.IndexIDMap2(faiss.IndexFlatIP(dimension))

    def _normalize(self, vectors: list[list[float]]):
        arr = self._np.array(vectors, dtype="float32")
        norms = self._np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms

    def upsert(self, ids: list[str], vectors: list[list[float]], metadatas: list[dict]) -> None:
        with self._lock:
            arr = self._normalize(vectors)
            rows = []
            for _id, meta in zip(ids, metadatas):
                row = self._id_to_row.get(_id)
                if row is None:
                    row = len(self._id_to_row)
                    self._id_to_row[_id] = row
                self._row_to_meta[row] = {**meta, "_id": _id}
                rows.append(row)

            row_ids = self._np.array(rows, dtype="int64")
            self._index.remove_ids(row_ids)
            self._index.add_with_ids(arr, row_ids)
            self._persist()

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        with self._lock:
            if self._index.ntotal == 0:
                return []
            arr = self._normalize([query_vector])
            scores, rows = self._index.search(arr, min(top_k, self._index.ntotal))
            results = []
            for score, row in zip(scores[0], rows[0]):
                if row == -1:
                    continue
                meta = self._row_to_meta.get(int(row), {})
                results.append(SearchResult(id=meta.get("_id", str(row)), score=float(score), metadata=meta))
            return results

    def delete(self, ids: list[str]) -> None:
        with self._lock:
            rows = [self._id_to_row.pop(_id) for _id in ids if _id in self._id_to_row]
            for row in rows:
                self._row_to_meta.pop(row, None)
            if rows:
                self._index.remove_ids(self._np.array(rows, dtype="int64"))
                self._persist()

    def _persist(self) -> None:
        self._faiss.write_index(self._index, self._index_path)
        with open(self._meta_path, "w", encoding="utf-8") as f:
            json.dump({"id_to_row": self._id_to_row, "row_to_meta": self._row_to_meta}, f)


class PineconeVectorStore(VectorStore):
    """Managed cloud vector store adapter. Requires a real `PINECONE_API_KEY`."""

    def __init__(self, api_key: str, index_name: str, dimension: int):
        from pinecone import Pinecone  # noqa: PLC0415

        self._pc = Pinecone(api_key=api_key)
        if index_name not in [i["name"] for i in self._pc.list_indexes()]:
            self._pc.create_index(name=index_name, dimension=dimension, metric="cosine")
        self._index = self._pc.Index(index_name)

    def upsert(self, ids: list[str], vectors: list[list[float]], metadatas: list[dict]) -> None:
        self._index.upsert(vectors=list(zip(ids, vectors, metadatas)))

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        response = self._index.query(vector=query_vector, top_k=top_k, include_metadata=True)
        return [
            SearchResult(id=match["id"], score=match["score"], metadata=match.get("metadata", {}))
            for match in response["matches"]
        ]

    def delete(self, ids: list[str]) -> None:
        self._index.delete(ids=ids)


class WeaviateVectorStore(VectorStore):
    """Managed/self-hosted Weaviate adapter. Requires `WEAVIATE_URL` (and
    `WEAVIATE_API_KEY` for cloud instances)."""

    def __init__(self, url: str, api_key: str, class_name: str = "ContextPilotChunk"):
        import weaviate  # noqa: PLC0415

        auth = weaviate.auth.AuthApiKey(api_key) if api_key and "REPLACE_WITH" not in api_key else None
        self._client = weaviate.connect_to_custom(http_host=url, auth_credentials=auth)
        self._class_name = class_name

    def upsert(self, ids: list[str], vectors: list[list[float]], metadatas: list[dict]) -> None:
        collection = self._client.collections.get(self._class_name)
        with collection.batch.dynamic() as batch:
            for _id, vector, meta in zip(ids, vectors, metadatas):
                batch.add_object(properties=meta, uuid=_id, vector=vector)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        collection = self._client.collections.get(self._class_name)
        response = collection.query.near_vector(near_vector=query_vector, limit=top_k)
        return [
            SearchResult(id=str(obj.uuid), score=getattr(obj.metadata, "distance", 0.0), metadata=obj.properties)
            for obj in response.objects
        ]

    def delete(self, ids: list[str]) -> None:
        collection = self._client.collections.get(self._class_name)
        collection.data.delete_many(where={"path": ["id"], "operator": "ContainsAny", "valueTextArray": ids})


def get_vector_store(settings, dimension: int) -> VectorStore:
    provider = settings.vector_store_provider
    if provider == "faiss":
        return FAISSVectorStore(settings.vector_store_dir, dimension)
    if provider == "pinecone":
        return PineconeVectorStore(settings.pinecone_api_key, settings.pinecone_index_name, dimension)
    if provider == "weaviate":
        return WeaviateVectorStore(settings.weaviate_url, settings.weaviate_api_key)
    raise ValueError(f"Unknown VECTOR_STORE_PROVIDER: {provider}")
