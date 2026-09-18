"""SQS job queue (spec 06 REQ-004). Jobs survive worker restarts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID, uuid4

import boto3
from botocore.client import BaseClient

from app.config import get_settings

JOB_INGEST_REGULATION = "ingest_regulation"
JOB_INGEST_POLICY = "ingest_policy"
JOB_RUN_ANALYSIS = "run_analysis"


@dataclass(frozen=True)
class QueueMessage:
    receipt_handle: str
    body: dict[str, Any]


@lru_cache
def sqs_client() -> BaseClient:
    settings = get_settings()
    return boto3.client("sqs", region_name=settings.aws_region)


def enqueue_job(job_type: str, payload: dict[str, Any]) -> str:
    settings = get_settings()
    if not settings.sqs_queue_url:
        raise RuntimeError("SQS_QUEUE_URL is not configured")
    body = {"job_type": job_type, **payload}
    message_id = str(uuid4())
    sqs_client().send_message(
        QueueUrl=settings.sqs_queue_url,
        MessageBody=json.dumps(body, default=str),
        MessageAttributes={
            "job_type": {"StringValue": job_type, "DataType": "String"},
        },
    )
    return message_id


def enqueue_ingest_regulation(document_id: UUID) -> str:
    return enqueue_job(JOB_INGEST_REGULATION, {"document_id": str(document_id)})


def enqueue_ingest_policy(document_id: UUID, company_id: UUID) -> str:
    return enqueue_job(
        JOB_INGEST_POLICY,
        {"document_id": str(document_id), "company_id": str(company_id)},
    )


def enqueue_run_analysis(analysis_id: UUID, company_id: UUID) -> str:
    return enqueue_job(
        JOB_RUN_ANALYSIS,
        {"analysis_id": str(analysis_id), "company_id": str(company_id)},
    )


def receive_jobs(max_messages: int = 5, wait_seconds: int = 20) -> list[QueueMessage]:
    settings = get_settings()
    response = sqs_client().receive_message(
        QueueUrl=settings.sqs_queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=wait_seconds,
        MessageAttributeNames=["All"],
    )
    messages = []
    for raw in response.get("Messages", []):
        messages.append(
            QueueMessage(
                receipt_handle=raw["ReceiptHandle"],
                body=json.loads(raw["Body"]),
            )
        )
    return messages


def delete_job(receipt_handle: str) -> None:
    settings = get_settings()
    sqs_client().delete_message(QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt_handle)


def extend_visibility(receipt_handle: str, seconds: int) -> None:
    settings = get_settings()
    sqs_client().change_message_visibility(
        QueueUrl=settings.sqs_queue_url,
        ReceiptHandle=receipt_handle,
        VisibilityTimeout=seconds,
    )


def reset_sqs_client() -> None:
    sqs_client.cache_clear()
