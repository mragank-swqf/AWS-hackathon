---
name: implement-spec
description: >
  Implements the already-written RegImpact specs in spec/ as working code. Does not
  interview, does not write new product specs, does not wait for approval. Reads
  numbered files spec/01 through spec/17, builds one MVP stage at a time, then
  verifies with pytest and ruff. Use when the user asks to implement the specs,
  implement spec, start coding, build the product, build the MVP, hackathon build,
  spec-driven implement, continue implementation, resume implementation, code from
  the specs, or build stage 1, stage 2, stage 3, stage 4, stage 5, stage 6.
  Also use for database, API, upload, ingestion, RAG, agents, frontend, or
  "make it from the specs".
version: 2.2.0
---

Follow `.cursor/skills/implement-spec/SKILL.md` as the full runbook.

- Build only what the current stage's specs ask for. No extra stack, screens, or libraries.
- Do not use SQLite, local disk, an inline queue, or fake Bedrock.
- If Docker or AWS is not installed, still write the spec code. List installs at the end. Do not stop.
