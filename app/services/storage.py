"""Private S3 document storage (spec 06, spec 07 SEC-001). Never a public object ACL."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.aws import client, reset_clients
from app.config import get_settings


@lru_cache
def s3_client() -> BaseClient:
    return client("s3")


def regulation_key(document_id: UUID, filename: str) -> str:
    return f"regulations/{document_id}/{filename}"


def policy_key(company_id: UUID, document_id: UUID, filename: str) -> str:
    return f"policies/{company_id}/{document_id}/{filename}"


def put_private_pdf(key: str, data: bytes) -> None:
    settings = get_settings()
    s3_client().put_object(
        Bucket=settings.s3_document_bucket,
        Key=key,
        Body=data,
        ContentType="application/pdf",
        ServerSideEncryption="AES256",
    )


def get_object_bytes(key: str) -> bytes:
    settings = get_settings()
    response = s3_client().get_object(Bucket=settings.s3_document_bucket, Key=key)
    return response["Body"].read()


def delete_object(key: str) -> None:
    settings = get_settings()
    s3_client().delete_object(Bucket=settings.s3_document_bucket, Key=key)


def presigned_get_url(key: str) -> str:
    settings = get_settings()
    try:
        return s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_document_bucket, "Key": key},
            ExpiresIn=settings.presign_ttl_seconds,
        )
    except ClientError as exc:
        raise RuntimeError("Could not create a signed download link") from exc


def reset_s3_client() -> None:
    s3_client.cache_clear()
    reset_clients()
