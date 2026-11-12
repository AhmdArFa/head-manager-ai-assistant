# Step-by-step roadmap

Each phase should finish with a working API endpoint and tests before the next capability is added.

## Step 1 — Data Q&A foundation (prepared locally)

- `POST /api/v1/ask` routes questions through a small Chief Orchestrator to a focused Data Agent.
- The Data Agent executes only reviewed, read-only SQL from a fixed query catalog.
- The response includes its evidence table and a short execution trace.
- Local SQLite is seeded with explicitly synthetic data so the API can run without private credentials.
- **Acceptance:** health check and representative English/Arabic questions pass API tests; unsupported requests are not fabricated.

## Step 2 — Connect an approved company database

- Select the real database and map its approved tables/columns.
- Configure a least-privilege, read-only connection and bounded query timeouts/row counts.
- Add schema-specific reviewed queries and integration tests; do not expose arbitrary SQL.
- **Endpoint:** keep `/api/v1/ask` stable while replacing the demo Data Agent backend.
- **Needs user/company input:** database type, schema, connectivity method and authorized read-only access. No values are assumed in this starter.

## Step 3 — Add a second focused capability

- Add a document Research Agent only after choosing allowed document sources.
- Route structured-data questions and document questions separately; preserve source identifiers and permission filtering.
- **Endpoint:** `/api/v1/ask` continues returning an answer with typed source records; add a source lookup endpoint only if the UI needs it.

## Step 4 — Multi-agent planning and synthesis

- Replace deterministic routing with a validated planner only when multi-step questions justify it.
- Add bounded execution, shared typed state, retries and evidence synthesis.
- Keep the initial data path available as a deterministic fallback.
- **Endpoint:** `/api/v1/ask` remains the stable user-facing API.

## Step 5 — Actions only behind approval

- If actions are needed, expose proposed actions separately from execution.
- Require explicit human approval and backend-enforced permissions before any external side effect.
- **Endpoint:** add approval/decision routes only with an agreed action use case and tested controls.
