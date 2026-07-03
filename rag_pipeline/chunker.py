"""Token-aware document chunking with overlap."""
from dataclasses import dataclass

try:
    import tiktoken

    _ENCODER = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - tiktoken not available offline
    _ENCODER = None


@dataclass
class TextChunk:
    index: int
    content: str
    token_count: int


def _token_count(text: str) -> int:
    if _ENCODER is not None:
        return len(_ENCODER.encode(text))
    return max(1, len(text) // 4)  # rough fallback: ~4 chars/token


def _split_words(text: str) -> list[str]:
    return text.split()


def chunk_text(text: str, chunk_size: int = 400, chunk_overlap: int = 50) -> list[TextChunk]:
    """Split `text` into overlapping chunks targeting ~`chunk_size` tokens each.

    Uses a word-based sliding window scaled by the average tokens/word ratio,
    so it works even when a tokenizer isn't available (e.g. offline installs).
    """
    if not text or not text.strip():
        return []

    words = _split_words(text)
    if not words:
        return []

    total_tokens = _token_count(text)
    tokens_per_word = max(total_tokens / len(words), 0.1)
    words_per_chunk = max(int(chunk_size / tokens_per_word), 20)
    words_overlap = max(int(chunk_overlap / tokens_per_word), 0)

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(words):
        end = min(start + words_per_chunk, len(words))
        segment = " ".join(words[start:end])
        chunks.append(TextChunk(index=index, content=segment, token_count=_token_count(segment)))
        index += 1
        if end == len(words):
            break
        start = end - words_overlap

    return chunks
