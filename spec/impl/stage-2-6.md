# Stages 2–6 implementation log

Date: 2026-09-18
Stages: 2 (ingest + RAG), 3–4 (agents + impact), 5 (verification), 6 (demo)

## Stage 2
- `pypdf` text extraction. Unreadable pages are stored as chunks with `extraction_method=unreadable`.
- Clause-boundary chunking with token caps, overlap only when a clause is too big.
- Titan V2 embeddings through `TitanEmbedder`. Tests inject another embedder.
- Hybrid search: `pgvector` + `ts_rank_cd`, fused with RRF. Clause queries skip meaning search.
- Worker handlers ingest regulation and policy jobs.

## Stages 3–4
- Pydantic output shapes for all seven steps (`extra=forbid`).
- Runner saves each step to `impact_analyses.result` before the next.
- Risk is the table in spec 14. Confidence and `human_review_required` are runner-owned.
- Prompt fencing around uploaded text.

## Stage 5
- Claim check uses the claim and the chunk as two fenced inputs.
- `verification_status` from coverage / unsupported / contradicted cut-offs.
- Approve is refused until the analysis is `completed`.

## Stage 6
- Demo PDFs and `scripts/seed_demo.py` for PayFlow, grievance policy, KYC policy, and one circular.
- Results screen shows verification, failed step, teams, and date basis.

## Verify
`ruff check .` passed. `pytest`: 66 passed, 3 skipped (Postgres).

```bash
python scripts/seed_demo.py
# needs Postgres, S3 credentials, and Bedrock if ingest is not skipped
python scripts/seed_demo.py --skip-ingest
```
