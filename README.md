# RegImpact

RBI circulars are long. Someone on the compliance team still has to answer: does this apply to us, what are we missing, and who owns the fix?

**RegImpact** is an RBI-first regulatory intelligence tool for Indian fintechs, NBFCs, and payment aggregators. It maintains a corpus of official RBI publications, determines which regulations are relevant to a company, analyzes the company's own policy documents as evidence, identifies gaps, assesses risk, and turns findings into actionable remediation tasks.

It is a human-review system. It is not legal advice and does not file anything with a regulator.

## What it does

1. **Maintains an RBI corpus** — a seeded pack makes demos deterministic, while a background crawler can discover publications from `rbi.org.in`.
2. **Determines applicability** — company profile + regulatory metadata + AI reasoning classify regulations as **applicable**, **not applicable**, or **uncertain**. Uncertain stays uncertain until a person reviews it.
3. **Uses company evidence** — policy PDFs are analyzed as evidence. Profile checkboxes are never treated as proof.
4. **Runs impact analysis** — requirements, impact, gaps, risk, actions, and citations.
5. **Tracks remediation** — findings become actionable tasks rather than a wall of generated text.
6. **Detects regulatory changes** — updated publications can be compared against previous versions and their impact on the company reassessed.

There is also a secondary path to upload a regulation PDF manually. That is not the main flow.

The demo company is **PayFlow Technologies**, a fictional payment aggregator. It is not Paytm and does not copy Paytm documents.

---

## Architecture

```text
Official RBI Sources
        ↓
Regulatory Ingestion
        ↓
Metadata + Versioning
        ↓
Postgres + pgvector + FTS
        ↓
RBI Regulatory Corpus
        │
        ├────────────── Company Profile
        │                       │
        └────────────── Company Evidence
                                ↓
                         Applicability
                                ↓
                         Requirements
                                ↓
                            Impact
                                ↓
                         Gap Detection
                                ↓
                              Risk
                                ↓
                         Action Planning
                                ↓
                          Verification
                                ↓
                         Human Review
```

The **compliance reasoning engine is regulator-agnostic**. RBI is the first domain specialization through its corpus, metadata, taxonomy, and applicability layer.

---

## Spec-Driven Development

RegImpact was built using a **spec-driven development approach**.

Instead of starting with an LLM call and adding features around it, the product and system behavior were defined first through **17 numbered specifications in `spec/`**.

```text
Product requirements
        ↓
Specifications
        ↓
Schemas + contracts
        ↓
Architecture
        ↓
Implementation
        ↓
Tests
```

Start with:

```text
spec/01-spec-schema-product-definition.md
```

The specifications define product behavior, data contracts, system boundaries, AI responsibilities, evidence rules, validation requirements, and workflow behavior.

This is particularly important for RegImpact because the LLM is only one component of the system.

```text
LLM
→ regulatory interpretation
→ requirement extraction
→ evidence reasoning
→ remediation generation

Deterministic code
→ schema validation
→ company scope
→ evidence constraints
→ risk calculation
→ workflow rules
→ versioning
```

The result is an AI system whose behavior is constrained by explicit contracts rather than relying entirely on model output.

---

## RAG + AI

RegImpact uses hybrid retrieval:

```text
Semantic search
      +
PostgreSQL full-text search
      ↓
Reciprocal Rank Fusion
      ↓
Relevant evidence
```

The analysis pipeline is split into structured stages:

```text
Applicability
      ↓
Requirements
      ↓
Impact
      ↓
Gap Detection
      ↓
Risk
      ↓
Action Plan
      ↓
Verification
```

Each stage uses structured output contracts rather than unrestricted free-form responses.

The verification layer checks generated claims against retrieved source evidence before they become verified findings.

---

## Evidence Model

A core design principle is:

> **Compliance claims must be grounded in evidence.**

The system separates:

```text
Regulatory evidence
        vs
Company evidence
```

A company profile declaration is not sufficient evidence.

A finding should therefore connect:

```text
Regulatory requirement
        +
Company evidence
        ↓
Assessment
        ↓
Risk
        ↓
Action
```

Unsupported or uncertain findings can be escalated for human review.

---

## Regulatory Change Detection

The regulatory pipeline is designed to handle updates rather than treating every PDF as static.

```text
New / updated RBI publication
        ↓
Version detection
        ↓
Requirement comparison
        ↓
Affected companies
        ↓
Existing evidence
        ↓
New / modified gaps
        ↓
Risk + remediation
```

This allows the product to answer not only:

> "What does this regulation say?"

but:

> **"What changed, does it affect my company, and what do I need to do?"**

---

## Stack

| Piece          | Technology                                |
| -------------- | ----------------------------------------- |
| UI             | React + Vite                              |
| API            | FastAPI                                   |
| AI             | AWS Bedrock / configurable local provider |
| Jobs           | Python worker + SQS                       |
| Database       | PostgreSQL 16 + pgvector                  |
| Search         | pgvector + PostgreSQL FTS                 |
| Files          | S3                                        |
| Queue          | SQS                                       |
| Local AWS      | LocalStack                                |
| Secrets        | AWS Secrets Manager                       |
| Observability  | CloudWatch                                |
| Infrastructure | AWS + Docker                              |

---

## Run Locally

Requirements: Docker Desktop, Git, Node 18+.

```bash
git clone https://github.com/mragank-swqf/AWS-hackathon
cd AWS-hackathon

cp .env.example .env
docker compose up --build
```

Leave `LLM_PROVIDER=local` and `EMBEDDING_PROVIDER=local` unless you have working Bedrock/OpenAI credentials.

In another terminal:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_demo.py

cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Attach the seeded PayFlow company:

```js
localStorage.setItem("regimpact_company_id", "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
location.reload()
```

Then:

1. Open **Dashboard**
2. Click **Refresh RBI corpus**
3. Wait for applicable circulars
4. Click **Run impact**

After restart:

```bash
docker compose down
```

keeps database/files.

```bash
docker compose down -v
```

removes them and requires reseeding.

---

## Screens

| Screen              | Purpose                                |
| ------------------- | -------------------------------------- |
| Dashboard           | Corpus status and impact runs          |
| Applicable          | Relevant regulations + human overrides |
| Updates             | Regulatory versions and clause changes |
| Company Profile     | Company characteristics                |
| Company Evidence    | Policy PDFs available for analysis     |
| Compliance Analysis | Requirements, gaps, risk and sources   |
| Actions             | Remediation task list                  |

---

## Testing

```bash
docker compose exec api pytest
docker compose exec api ruff check .
```

Tests cover areas including:

* agent contracts
* schema validation
* company isolation
* evidence rules
* retrieval
* ingestion
* risk calculation
* review rules
* API validation
* uploads
* regulatory workflow behavior

The specifications define expected behavior; tests verify that the implementation conforms to those specifications.

---

## Design Principles

**Evidence over assertions**
Company declarations are not treated as evidence.

**Human review over false certainty**
Uncertain applicability or unsupported findings remain reviewable.

**Deterministic rules where they matter**
Risk, validation, scope, and workflow constraints are not left entirely to the LLM.

**AI where language reasoning is required**
LLMs handle regulatory interpretation, requirement extraction, evidence reasoning, and remediation generation.

**Traceability**
Findings link back to regulatory source text and company evidence.

**Modular regulatory support**
RBI is the initial domain; the core compliance engine remains regulator-agnostic.

**Specifications before implementation**
Product behavior and system contracts are defined in `spec/` and validated through tests.

---

## Limitations

RegImpact is a hackathon prototype.

It is not legal advice, a substitute for a compliance officer, a regulatory filing system, or a guarantee of compliance.

The quality of findings depends on the coverage and accuracy of the regulatory corpus and company evidence.

## License

MIT. See `LICENSE`.
