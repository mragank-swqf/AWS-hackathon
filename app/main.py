import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.aws import client

app = FastAPI(title="RegImpact API")


class JobRequest(BaseModel):
    company_id: str = "company_001"
    regulation_id: str | None = None
    note: str = "localstack demo job"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/jobs")
def enqueue_job(body: JobRequest):
    job_id = str(uuid.uuid4())
    payload = {
        "job_id": job_id,
        "company_id": body.company_id,
        "regulation_id": body.regulation_id,
        "note": body.note,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    key = f"jobs/{job_id}.json"

    try:
        s3 = client("s3")
        sqs = client("sqs")
        s3.put_object(
            Bucket=os.environ["S3_BUCKET"],
            Key=key,
            Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json",
        )
        sqs.send_message(
            QueueUrl=os.environ["SQS_QUEUE_URL"],
            MessageBody=json.dumps({"job_id": job_id, "s3_key": key}),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LocalStack enqueue failed: {exc}") from exc

    return {"job_id": job_id, "s3_key": key, "status": "queued"}
