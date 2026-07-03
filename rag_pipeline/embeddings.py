"""Pluggable embedding clients.

`OpenAIEmbeddingClient` calls the real OpenAI embeddings API and is used
whenever a real `OPENAI_API_KEY` is configured. `LocalHashEmbeddingClient`
is a deterministic, dependency-free fallback (feature-hashing into a fixed
dimensional vector) that lets the whole RAG pipeline run offline/in CI/in a
fresh clone before a client has swapped in real credentials.
"""
import hashlib
import math
import re
from typing import Protocol

EMBEDDING_DIM = 384
_PLACEHOLDER_MARKERS = ("REPLACE_WITH", "sk-REPLACE", "sk-ant-REPLACE")


class EmbeddingClient(Protocol):
    dimension: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class OpenAIEmbeddingClient:
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model
        self.dimension = 1536 if "small" in model else 3072

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class LocalHashEmbeddingClient:
    """Deterministic bag-of-tokens hashing embedding. Not semantically strong,
    but stable, offline, and good enough for local dev / smoke tests / CI."""

    dimension = EMBEDDING_DIM

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


def is_placeholder_key(key: str) -> bool:
    return not key or any(marker in key for marker in _PLACEHOLDER_MARKERS)


def get_embedding_client(settings) -> EmbeddingClient:
    if settings.llm_provider == "openai" and not is_placeholder_key(settings.openai_api_key):
        return OpenAIEmbeddingClient(settings.openai_api_key, settings.openai_embedding_model)
    return LocalHashEmbeddingClient()
