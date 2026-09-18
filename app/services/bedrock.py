"""Amazon Bedrock client. Real boto3 calls only — no fake model (spec 06)."""

from __future__ import annotations

import json
from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.config import get_settings


class BedrockUnavailableError(RuntimeError):
    pass


@lru_cache
def bedrock_runtime_client() -> BaseClient:
    settings = get_settings()
    return boto3.client("bedrock-runtime", region_name=settings.aws_region)


def _raise_model_unavailable(model_id: str, exc: ClientError) -> None:
    settings = get_settings()
    code = exc.response.get("Error", {}).get("Code", "Unknown")
    raise BedrockUnavailableError(
        f"Bedrock model '{model_id}' is not available in {settings.aws_region} "
        f"({code}). Enable Claude Sonnet and Titan Text Embeddings V2 in us-east-1 "
        "before running analysis."
    ) from exc


def invoke_claude(prompt: str, max_tokens: int = 2048) -> str:
    settings = get_settings()
    model_id = settings.bedrock_llm_model
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        response = bedrock_runtime_client().invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
    except ClientError as exc:
        _raise_model_unavailable(model_id, exc)
    payload = json.loads(response["body"].read())
    parts = payload.get("content") or []
    return "".join(part.get("text", "") for part in parts if part.get("type") == "text")


def embed_titan(text: str) -> list[float]:
    settings = get_settings()
    model_id = settings.bedrock_embedding_model
    body = {"inputText": text, "dimensions": 1024, "normalize": True}
    try:
        response = bedrock_runtime_client().invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
    except ClientError as exc:
        _raise_model_unavailable(model_id, exc)
    payload = json.loads(response["body"].read())
    embedding = payload.get("embedding")
    if not isinstance(embedding, list) or len(embedding) != 1024:
        raise BedrockUnavailableError(
            f"Titan embedding for '{model_id}' did not return 1024 numbers"
        )
    return embedding


def reset_bedrock_client() -> None:
    bedrock_runtime_client.cache_clear()
