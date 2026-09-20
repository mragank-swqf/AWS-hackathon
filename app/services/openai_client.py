"""OpenAI Chat + embeddings. Used when Bedrock quotas are blocked."""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger("regimpact.openai")

OPENAI_URL = "https://api.openai.com/v1"


class OpenAIUnavailableError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    settings = get_settings()
    key = (settings.openai_api_key or "").strip()
    if not key:
        raise OpenAIUnavailableError(
            "OPENAI_API_KEY is empty. Paste the key into .env (do not put it in chat)."
        )
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def invoke_openai_chat(prompt: str, max_tokens: int = 4096) -> str:
    settings = get_settings()
    body = {
        "model": settings.openai_llm_model,
        "messages": [
            {"role": "system", "content": "Return valid JSON only. No markdown."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    try:
        response = httpx.post(
            f"{OPENAI_URL}/chat/completions",
            headers=_headers(),
            json=body,
            timeout=120.0,
        )
    except httpx.HTTPError as exc:
        raise OpenAIUnavailableError(f"OpenAI chat request failed: {exc}") from exc
    if response.status_code >= 400:
        raise OpenAIUnavailableError(
            f"OpenAI chat {response.status_code}: {response.text[:400]}"
        )
    payload = response.json()
    choices = payload.get("choices") or []
    if not choices:
        raise OpenAIUnavailableError("OpenAI chat returned no choices")
    text = (choices[0].get("message") or {}).get("content") or ""
    if not text.strip():
        raise OpenAIUnavailableError("OpenAI chat returned empty text")
    return text


def embed_openai(text: str) -> list[float]:
    settings = get_settings()
    body = {
        "model": settings.openai_embedding_model,
        "input": text[:8000],
        "dimensions": 1024,
    }
    try:
        response = httpx.post(
            f"{OPENAI_URL}/embeddings",
            headers=_headers(),
            json=body,
            timeout=60.0,
        )
    except httpx.HTTPError as exc:
        raise OpenAIUnavailableError(f"OpenAI embedding request failed: {exc}") from exc
    if response.status_code >= 400:
        raise OpenAIUnavailableError(
            f"OpenAI embeddings {response.status_code}: {response.text[:400]}"
        )
    data = (response.json().get("data") or [{}])[0]
    embedding = data.get("embedding")
    if not isinstance(embedding, list) or len(embedding) != 1024:
        raise OpenAIUnavailableError("OpenAI embedding did not return 1024 numbers")
    return embedding
