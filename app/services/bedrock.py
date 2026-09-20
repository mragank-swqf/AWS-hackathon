"""Amazon Bedrock client. Real boto3 calls only — no fake model (spec 06)."""

from __future__ import annotations

import json
import logging
import time
from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger("regimpact.bedrock")

_THROTTLE_CODES = frozenset(
    {"ThrottlingException", "TooManyRequestsException", "ServiceUnavailableException"}
)
_RETRY_DELAYS_SECONDS = (45, 90)


class BedrockUnavailableError(RuntimeError):
    pass


@lru_cache
def bedrock_runtime_client() -> BaseClient:
    settings = get_settings()
    # AWS_ENDPOINT_URL is LocalStack for S3/SQS. Bedrock is not in LocalStack.
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        config=Config(
            ignore_configured_endpoint_urls=True,
            retries={"max_attempts": 1, "mode": "standard"},
        ),
    )


def _raise_model_unavailable(model_id: str, exc: ClientError) -> None:
    settings = get_settings()
    code = exc.response.get("Error", {}).get("Code", "Unknown")
    raise BedrockUnavailableError(
        f"Bedrock model '{model_id}' is not available in {settings.aws_region} "
        f"({code}). Enable Claude Sonnet and Titan Text Embeddings V2 in us-east-1 "
        "before running analysis."
    ) from exc


def _invoke_model(model_id: str, body: dict) -> dict:
    last_error: ClientError | None = None
    for delay in (0, *_RETRY_DELAYS_SECONDS):
        if delay:
            logger.info("Bedrock throttled %s; waiting %ss", model_id, delay)
            time.sleep(delay)
        try:
            response = bedrock_runtime_client().invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            return json.loads(response["body"].read())
        except ClientError as exc:
            last_error = exc
            code = exc.response.get("Error", {}).get("Code", "")
            if code not in _THROTTLE_CODES:
                _raise_model_unavailable(model_id, exc)
    assert last_error is not None
    _raise_model_unavailable(model_id, last_error)


def invoke_claude(prompt: str, max_tokens: int = 2048) -> str:
    settings = get_settings()
    model_id = settings.bedrock_llm_model
    payload = _invoke_model(
        model_id,
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    parts = payload.get("content") or []
    return "".join(part.get("text", "") for part in parts if part.get("type") == "text")


def embed_titan(text: str) -> list[float]:
    settings = get_settings()
    model_id = settings.bedrock_embedding_model
    payload = _invoke_model(
        model_id,
        {"inputText": text, "dimensions": 1024, "normalize": True},
    )
    embedding = payload.get("embedding")
    if not isinstance(embedding, list) or len(embedding) != 1024:
        raise BedrockUnavailableError(
            f"Titan embedding for '{model_id}' did not return 1024 numbers"
        )
    return embedding


def reset_bedrock_client() -> None:
    bedrock_runtime_client.cache_clear()
