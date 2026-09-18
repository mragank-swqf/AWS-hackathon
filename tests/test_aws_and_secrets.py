from uuid import uuid4

import boto3
import pytest
from app.config import get_settings
from app.services.bedrock import BedrockUnavailableError, embed_titan, invoke_claude
from app.services.queue import enqueue_ingest_regulation, receive_jobs
from app.services.storage import put_private_pdf, reset_s3_client, s3_client
from botocore.exceptions import ClientError
from moto import mock_aws


@mock_aws
def test_private_put_does_not_set_public_acl():
    settings = get_settings()
    reset_s3_client()
    client = boto3.client("s3", region_name=settings.aws_region)
    client.create_bucket(Bucket=settings.s3_document_bucket)
    put_private_pdf("regulations/demo/file.pdf", b"%PDF-1.4")
    acl = s3_client().get_object_acl(Bucket=settings.s3_document_bucket, Key="regulations/demo/file.pdf")
    grants = [grant["Permission"] for grant in acl.get("Grants", [])]
    # Default object owner FULL_CONTROL is fine; public READ must not appear.
    uris = [grant.get("Grantee", {}).get("URI", "") for grant in acl.get("Grants", [])]
    assert not any("AllUsers" in uri or "AuthenticatedUsers" in uri for uri in uris)
    assert "FULL_CONTROL" in grants or grants == []


@mock_aws
def test_sqs_keeps_jobs(monkeypatch):
    settings = get_settings()
    sqs = boto3.client("sqs", region_name=settings.aws_region)
    queue = sqs.create_queue(QueueName="regimpact-jobs")
    monkeypatch.setenv("SQS_QUEUE_URL", queue["QueueUrl"])
    get_settings.cache_clear()
    from app.services.queue import reset_sqs_client

    reset_sqs_client()
    enqueue_ingest_regulation(uuid4())
    messages = receive_jobs(wait_seconds=1)
    assert len(messages) == 1
    assert messages[0].body["job_type"] == "ingest_regulation"


def test_bedrock_missing_model_is_explicit(monkeypatch):
    class FakeClient:
        def invoke_model(self, **_kwargs):
            error = ClientError(
                {"Error": {"Code": "ResourceNotFoundException", "Message": "nope"}},
                "InvokeModel",
            )
            raise error

    monkeypatch.setattr("app.services.bedrock.bedrock_runtime_client", lambda: FakeClient())
    with pytest.raises(BedrockUnavailableError) as exc:
        invoke_claude("hello")
    assert "us-east-1" in str(exc.value)
    with pytest.raises(BedrockUnavailableError):
        embed_titan("hello")


def test_settings_come_from_environment(monkeypatch):
    monkeypatch.setenv("S3_DOCUMENT_BUCKET", "env-bucket")
    get_settings.cache_clear()
    assert get_settings().s3_document_bucket == "env-bucket"
    get_settings.cache_clear()
