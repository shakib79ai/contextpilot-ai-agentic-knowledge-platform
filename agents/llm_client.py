"""Chat-completion client abstraction shared by the Answer, Evaluator, and
Knowledge Update agents. Returns `None` when no real provider key is
configured so callers can fall back to a deterministic, offline-friendly
heuristic instead of crashing on a dummy placeholder key.
"""
from typing import Protocol

from rag_pipeline.embeddings import is_placeholder_key


class ChatClient(Protocol):
    def complete(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 800) -> str: ...


class OpenAIChatClient:
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 800) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


class AnthropicChatClient:
    def __init__(self, api_key: str, model: str):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 800) -> str:
        response = self._client.messages.create(
            model=self._model,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return "".join(block.text for block in response.content if block.type == "text")


def get_chat_client(settings) -> ChatClient | None:
    if settings.llm_provider == "openai" and not is_placeholder_key(settings.openai_api_key):
        return OpenAIChatClient(settings.openai_api_key, settings.openai_chat_model)
    if settings.llm_provider == "anthropic" and not is_placeholder_key(settings.anthropic_api_key):
        return AnthropicChatClient(settings.anthropic_api_key, settings.anthropic_model)
    return None
