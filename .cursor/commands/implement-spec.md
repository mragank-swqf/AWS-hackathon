Implement the already-written RegImpact specs as working code.

Follow `.cursor/skills/implement-spec/SKILL.md` exactly.

- Do not interview. Do not write a new product spec. Do not wait for approval.
- Do not edit `spec/01` through `spec/17`. Progress logs go in `spec/impl/` only.
- Read `spec/01`–`spec/04` first, then the files for the current stage.
- Build only what those specs ask for. No extra features, no second local stack.
- Build one MVP stage at a time. If no stage is named, start at the first incomplete stage (default Stage 1).
- If I named a stage or said continue, do that stage only.
- If I said implement all specs, finish stages 1 through 6, then the spec 17 gate.
- Write Postgres, S3, SQS, and Bedrock code even if Docker and AWS are not installed yet. Do not stop. List what to install at the end.
- Start coding in this turn. Run `pytest` and `ruff check .` if you can.
- Do not commit unless I asked.
