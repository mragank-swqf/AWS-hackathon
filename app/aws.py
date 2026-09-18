"""Shared boto3 clients. LocalStack when AWS_ENDPOINT_URL is set; real AWS otherwise."""

from __future__ import annotations

from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from app.config import get_settings


@lru_cache
def client(service: str) -> BaseClient:
    settings = get_settings()
    kwargs: dict = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
        if service == "s3":
            kwargs["config"] = Config(s3={"addressing_style": "path"})
    return boto3.client(service, **kwargs)


def reset_clients() -> None:
    client.cache_clear()
