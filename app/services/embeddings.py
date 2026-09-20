"""Embedding wrapper. Titan, OpenAI, or a test double (spec 11 REQ-007)."""

from __future__ import annotations

import time
from typing import Protocol

from app.config import get_settings
from app.services.bedrock import embed_titan
from app.services.local_ai import local_embed
from app.services.openai_client import embed_openai

_EMBED_GAP_SECONDS = 0.05


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class TitanEmbedder:
    def embed(self, text: str) -> list[float]:
        vector = embed_titan(text[:8000])
        time.sleep(_EMBED_GAP_SECONDS)
        return vector


class OpenAIEmbedder:
    def embed(self, text: str) -> list[float]:
        return embed_openai(text)


class LocalEmbedder:
    def embed(self, text: str) -> list[float]:
        return local_embed(text)


def default_embedder() -> Embedder:
    provider = get_settings().embedding_provider
    if provider == "openai":
        return OpenAIEmbedder()
    if provider == "local":
        return LocalEmbedder()
    return TitanEmbedder()
