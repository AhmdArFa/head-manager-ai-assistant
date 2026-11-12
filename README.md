# Head Manager AI Assistant

A small, extensible Chief Orchestrator starter for answering company questions from structured data. The first deliverable is intentionally narrow: a working FastAPI endpoint backed by a local SQLite database, with a deterministic data agent and traceable source metadata.

> **Data notice:** the included database is seeded with clearly synthetic demo records. This starter does not connect to Ahmed's employer or any real company system yet. No company credentials or schema were provided, so connecting private organizational data is a later, explicit step.

## First working step

`POST /api/v1/ask` accepts a business question, routes it through the Chief Orchestrator to the Data Agent, runs a reviewed read-only SQL query from a fixed catalog, and returns an answer with the queried table and row count. Unknown question types are reported honestly rather than guessed.

Assistant answer text is written in natural colloquial Egyptian Arabic. Names, job titles, department names, and database statuses remain as stored in the source data; the evidence and execution trace are unchanged.

Current supported questions include:

- “How many employees do we have?” / “كام موظف عندنا؟”
- “Who works in Engineering?” / “مين في قسم Engineering؟”
- “What is the status of our projects?” / “حالة المشاريع إيه؟”
- “What open tasks need attention?” / “ما هي المهام المفتوحة؟”

The endpoint does not accept or execute SQL supplied by a user or language model. The database connection used for answering questions opens in SQLite read-only mode. The sample records are synthetic and intended only to make the API runnable and testable.

## Run locally

Requires Python 3.10 or later.

```bash
python -m venv .venv
source .venv/bin/activate             # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The first run creates `data/company_demo.db` and seeds sample rows. Open `http://127.0.0.1:8000/docs` for interactive API docs.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ask \\
  -H 'Content-Type: application/json' \\
  -d '{"question":"How many employees do we have?"}'
```

The database path can be changed with `DATABASE_PATH`; copy `.env.example` as a reminder of the setting (environment variables are read directly, no dotenv package is required). The configured file must already contain the expected demo schema in this starter.

## Test

```bash
pip install -r requirements-dev.txt
pytest
```

## Structure

```text
app/
  agents/data_agent.py   Reviewed query catalog and grounded responses
  db.py                  SQLite schema, demo seed and read-only connection
  main.py                FastAPI app and /health, /api/v1/ask endpoints
  orchestrator.py        Small routing layer, designed for future agents
  schemas.py             Request/response contracts
 tests/                  API behavior tests using isolated temporary databases
 docs/roadmap.md          Step-by-step plan; each step ends in a working API
```

## Architecture and scope

```text
Client -> FastAPI -> Chief Orchestrator -> Data Agent -> read-only SQLite
                                        -> evidence + answer + trace -> Client
```

The modular boundaries borrow architectural ideas—not implementation code—from [Gnanasudharsan/enterprise-agentic-assistant](https://github.com/Gnanasudharsan/enterprise-agentic-assistant): a central supervisor, focused agents, grounded evidence, read-only data access, and incremental phases with a verified deliverable. This first version deliberately avoids LangGraph, an LLM, document retrieval, external integrations, and actions; adding those before the first endpoint works would add unnecessary setup and risk.

## Next steps

See [the roadmap](docs/roadmap.md). The next real-data milestone needs the target database type, an approved read-only account or connection mechanism, and the relevant table/schema details. Do not put production passwords in source control; use environment variables or a secrets manager when the integration is designed.
