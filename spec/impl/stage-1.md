# Stage 1 implementation log

Date: 2026-09-18
Stage: 1 (specs 05, 06, 07, 08, 09)

## Built

- PostgreSQL schema and Alembic migration `0001_initial` with `pgvector`, the ten tables, chunk XOR/tenant checks, HNSW + GIN indexes, and generated `tsvector`.
- FastAPI `/api/v1` endpoints from spec 08, JSON error shape, `X-Request-Id`, `X-Company-Id` tenant scoping.
- Private S3 uploads (AES-256, no public ACL), SQS enqueue for ingest/analysis jobs, Bedrock client via boto3 (Claude Sonnet + Titan v2, 1024-d).
- Upload type/size checks. Secrets from the environment only.
- Worker process that long-polls SQS and leaves unhandled jobs on the queue for Stage 2.
- React screens: Company Profile, Regulation Library, Evidence Library, Analysis Setup, Analysis Results, Action Tracker. No login, no dashboard.
- CloudFormation for private S3, SQS + DLQ, RDS Postgres, IAM, CloudWatch, CloudFront.

## Not in this stage

- PDF text extraction, chunking, embeddings (Stage 2).
- Agent steps and impact report body (Stages 3–4).
- Citation verification beyond the data model (Stage 5).
- Demo seed data (Stage 6).

## Verify

`ruff check .` passed. `pytest`: 25 passed, 3 skipped (database tests need Postgres + pgvector via `TEST_DATABASE_URL`).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
ruff check .
```

Database tests need Postgres + pgvector:

```bash
docker compose up -d
alembic upgrade head
TEST_DATABASE_URL=postgresql+psycopg2://regimpact:regimpact@localhost:5432/regimpact pytest -m db
```

## Run locally (after installs)

```bash
docker compose up -d
alembic upgrade head
uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

Enable Claude Sonnet and Titan Text Embeddings V2 in Bedrock `us-east-1` before analysis work.
