"""Embedding wrapper. Production uses Titan V2; tests swap this (spec 11 REQ-007)."""

from __future__ import annotations

from typing import Protocol

from app.services.bedrock import embed_titan


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class TitanEmbedder:
    def embed(self, text: str) -> list[float]:
        return embed_titan(text[:8000])
