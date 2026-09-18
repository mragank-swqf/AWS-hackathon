import json
import os
import time

import chromadb

from app.aws import client


def chroma_client():
    return chromadb.HttpClient(
        host=os.environ.get("CHROMA_HOST", "chroma"),
        port=int(os.environ.get("CHROMA_PORT", "8000")),
    )


def process_message(s3, body: dict) -> None:
    job_id = body["job_id"]
    key = body["s3_key"]
    obj = s3.get_object(Bucket=os.environ["S3_BUCKET"], Key=key)
    payload = json.loads(obj["Body"].read().decode("utf-8"))
    collection = chroma_client().get_or_create_collection("jobs")
    collection.upsert(
        ids=[job_id],
        documents=[json.dumps(payload)],
        metadatas=[{"source": "localstack-sqs"}],
    )
    print(f"processed job {job_id} from s3://{os.environ['S3_BUCKET']}/{key}", flush=True)


def run() -> None:
    s3 = client("s3")
    sqs = client("sqs")
    queue_url = os.environ["SQS_QUEUE_URL"]
    print(f"worker polling {queue_url}", flush=True)

    while True:
        try:
            resp = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=20,
                VisibilityTimeout=60,
            )
        except Exception as exc:
            print(f"sqs receive failed: {exc}", flush=True)
            time.sleep(5)
            continue

        for message in resp.get("Messages", []):
            try:
                process_message(s3, json.loads(message["Body"]))
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message["ReceiptHandle"],
                )
            except Exception as exc:
                print(f"job failed (will retry after visibility timeout): {exc}", flush=True)


if __name__ == "__main__":
    run()
