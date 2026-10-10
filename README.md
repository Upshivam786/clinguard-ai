# ClinGuard AI

**Privacy-first clinical information retrieval powered by RAG, PostgreSQL/pgvector, and large language models.**

ClinGuard AI is a portfolio project exploring how healthcare professionals can query patient-scoped clinical records using natural language. It combines semantic retrieval, grounded LLM generation, PII redaction, JWT authentication, and a Streamlit interface.

> **Disclaimer:** ClinGuard AI is an educational demonstration, not a validated clinical decision-support system. It must not be used to make real-world diagnosis or treatment decisions. It does not claim HIPAA compliance.

## Features

- **Clinical RAG:** Retrieves relevant clinical events and generates answers grounded in retrieved context.
- **Patient-scoped retrieval:** Supports explicit patient and optional admission filters, with application-level boundary checks.
- **Semantic search:** PostgreSQL, pgvector, and an HNSW vector index.
- **PII redaction:** Microsoft Presidio redacts detected names, email addresses, phone numbers, and IP addresses from user questions before retrieval and generation.
- **Authentication:** JWT-based API authentication with clinician and administrator demo accounts.
- **Clinical guardrails:** Reduces unsupported medication-administration claims and unsupported completeness statements.
- **Streamlit interface:** Provides sign-in, patient/admission selection, query submission, and answer display.
- **Docker deployment:** Runs the API, UI, and database with Docker Compose.
- **Automated tests:** Unit and integration tests for retrieval, context construction, patient boundaries, and response guardrails.

## Architecture

```text
Clinician
   |
   v
Streamlit UI (:8501)
   |
   | JWT-authenticated request
   v
FastAPI (:8000)
   |
   +--> Presidio PII redaction
   |
   +--> Patient/admission-scoped semantic retrieval
   |        |
   |        v
   |    PostgreSQL + pgvector
   |        |
   |        v
   |    HNSW vector index
   |
   +--> Question-aware context construction
   |
   +--> OpenRouter LLM
   |
   +--> Clinical response guardrails
   |
   v
Grounded answer and retrieval metadata
```

PostgreSQL is exposed on `127.0.0.1:5432` by default and is intended for internal use. The Streamlit UI communicates with FastAPI over the Docker network.

## Technology stack

| Component | Technology |
|---|---|
| API | Python, FastAPI, Uvicorn |
| Frontend | Streamlit |
| Database | PostgreSQL 16 |
| Vector search | pgvector, HNSW |
| LLM provider | OpenRouter |
| Generation model | `qwen/qwen3.7-plus` |
| Embedding model | `qwen/qwen3-embedding-8b` |
| Embedding dimension | 2,000 |
| Privacy | Microsoft Presidio, spaCy |
| Authentication | JWT, Passlib |
| Deployment | Docker, Docker Compose |
| Testing | pytest |

## Prerequisites

- Linux server or development machine with Docker Engine and Docker Compose.
- An OpenRouter API key with access to the configured models.
- Sufficient disk space for Docker images, PostgreSQL data, and the spaCy language model.
- The clinical dataset and its embeddings, if reproducing the populated demo database.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Upshivam786/clinguard-ai.git
cd clinguard-ai
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and replace every placeholder with an appropriate value.

Required settings include:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`
- `OPENROUTER_MODEL`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSION`
- `CLINGUARD_JWT_SECRET`
- `CLINGUARD_CLINICIAN_PASSWORD`
- `CLINGUARD_ADMIN_PASSWORD`

Generate a strong JWT secret, for example:

```bash
openssl rand -hex 32
```

Never commit `.env`, access tokens, API keys, or passwords.

### 3. Build and start the services

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

The API image installs the pinned `en_core_web_lg` 3.8.0 spaCy model during the image build. A fresh build therefore needs network access to download that model.

### 4. Verify service health

```bash
curl http://127.0.0.1:8000/health
curl -I http://127.0.0.1:8501
```

Expected API health response:

```json
{
  "status": "ok",
  "service": "clinguard-ai"
}
```

Open the Streamlit interface at:

`http://YOUR_SERVER_IP:8501`

For remote deployments, restrict firewall access to trusted IP addresses or use an SSH tunnel. Do not expose the UI or API publicly without suitable access controls and HTTPS.

## Authentication and API usage

### Log in

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=clinician" \
  --data-urlencode "password=YOUR_CLINICIAN_PASSWORD"
```

Use the returned `access_token` as a bearer token. Keep it private.

### Check the current user

```bash
curl http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Submit a clinical query

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What medications were documented?",
    "patient_id": 7,
    "admission_id": 11,
    "top_k": 100,
    "max_context_events": 8
  }'
```

The response includes the question, patient/admission scope, retrieved-event count, context-event count, and generated answer.

The example identifiers are specific to the demo dataset. They are not real patient identifiers to use in other environments.

## Privacy and safety design

### PII redaction

The application runs Presidio against the user's question before using it for semantic retrieval or LLM generation. The currently configured recognizers include:

- `PERSON`
- `EMAIL_ADDRESS`
- `PHONE_NUMBER`
- `IP_ADDRESS`

Detected entities are replaced with `<REDACTED>`.

PII detection is not perfect. It may miss identifiers, redact non-sensitive text, or behave differently across languages and formats. The current implementation does not constitute a comprehensive de-identification system.

The API response currently preserves the original question. Consequently, clients and downstream logs must not assume that the returned question is redacted.

### Clinical grounding

The generation prompt and response guardrails encourage the application to:

- Use retrieved context rather than inventing clinical facts.
- Communicate when available context is insufficient.
- Avoid unsupported claims that a medication was administered or received.
- Avoid interpreting event metadata as proof of a clinical action.
- Avoid claiming that retrieved records represent the complete medical history.

These controls reduce risk but cannot guarantee that every generated answer is correct.

### Authentication limitations

JWT authentication protects the API endpoints, but this portfolio implementation uses in-memory demo accounts and role metadata. It is not a complete identity-management or authorization system. The current query endpoint requires authentication but does not implement a comprehensive per-patient authorization policy.

Before any real clinical use, implement persistent user management, enforced role- and patient-level access control, key rotation, secure session handling, HTTPS, audit logging, and an appropriate security review.

## Dataset and limitations

This project was developed using a cleaned MIMIC-IV-derived clinical transcript/order dataset obtained from Kaggle for educational exploration.

The working demo database was populated separately from the application source. A fresh clone does not automatically contain the dataset, normalized clinical tables, or precomputed embeddings.

Do not commit raw clinical data, database dumps, embeddings, credentials, or other sensitive artifacts to GitHub. Review the dataset's license, provenance, and applicable terms before redistributing any data.

## Testing

The test suite is configured through `pytest.ini`.

Run tests in a development environment with the project dependencies and pytest installed:

```bash
python -m pytest -q
```

The existing suite covers:

- Patient and admission boundary validation.
- Context construction and metadata handling.
- Clinical response guardrails.
- Semantic retrieval integration.

The 17 existing tests passed in the development container during the documented deployment workflow. Re-run the tests after changing the code or environment; results may vary with dependencies and database availability.

## Project structure

```text
.
├── deployment/       # Database initialization and schema SQL
├── docs/             # System design, threat model, and test strategy
├── scripts/          # Retrieval and pipeline utilities
├── src/
│   ├── api/          # FastAPI routes and authentication
│   ├── embeddings/   # Embedding generation utilities
│   ├── guardrails/   # Clinical answer guardrails
│   ├── llm/          # LLM generation
│   ├── privacy/      # Presidio PII redaction
│   ├── rag/          # RAG orchestration
│   ├── retrieval/     # Semantic search and context construction
│   └── ui/           # Streamlit application
├── tests/
│   ├── integration/
│   └── unit/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Roadmap

- [x] PostgreSQL and pgvector integration.
- [x] Patient-scoped semantic retrieval.
- [x] Grounded RAG generation and response guardrails.
- [x] JWT-based API authentication.
- [x] Presidio PII redaction for user questions.
- [x] Dockerized API and Streamlit UI.
- [x] Initial automated test suite.
- [ ] Manual end-to-end validation of the Streamlit UI.
- [ ] Lightweight observability and evaluation.
- [ ] Further authorization and security hardening.

## Disclaimer

ClinGuard AI is an educational portfolio project. It is not a medical device, is not clinically validated, and must not be used as a substitute for qualified healthcare professionals or established clinical systems. It does not claim regulatory approval or HIPAA compliance.
