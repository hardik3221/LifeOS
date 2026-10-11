# LifeOS backend

A local, single-user prototype with persistent task and goal CRUD, validation, configurable local CORS, and a planner integration boundary. No frontend or LLM implementation is included.

## Install and run

Python 3.10+; validated on Python 3.12. Run all commands from the repository root:

```bash
python -m venv backend/.venv
source backend/.venv/bin/activate
# Windows PowerShell: backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs for Swagger UI, http://127.0.0.1:8000/redoc for ReDoc, or http://127.0.0.1:8000/openapi.json for the generated contract. `/health` probes database connectivity. The exact dependency versions used for validation are recorded in `requirements-tested.txt` (`pip install -r backend/requirements-tested.txt` to reproduce the test environment).

```bash
python -m pytest backend/tests -q
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Complete DSA practice","description":"Solve array problems","priority":"high","deadline":"2026-10-12T18:00:00+05:30","estimated_minutes":60,"completed":false}'
```

That deadline is sample data only. No demo data is inserted automatically; create any sample tasks through `/docs`. Each test uses an isolated database.

## Database and configuration

SQLite defaults to `lifeos.db` in the working directory and survives process restarts. Do not commit this database, virtual environments or `.env` files. Settings load from `backend/.env` or environment variables (environment takes precedence). `CORS_ORIGINS` is a JSON array of exact origins; defaults are `http://localhost:3000` and `http://localhost:5173`. Add `127.0.0.1` origins if your frontend uses those hosts. Credentials are disabled; authentication is not implemented in this prototype.

For PostgreSQL, provision a database and role, then set:

```dotenv
DATABASE_URL=postgresql+psycopg://lifeos:your-local-password@localhost:5432/lifeos
```

The psycopg driver is included. Startup creates missing tables on either database. This is initial schema bootstrapping, not schema migration: add versioned migrations before changing an existing database schema or deploying the multi-user MVP. PostgreSQL configuration is provided but no PostgreSQL server was available for integration validation; automated tests cover SQLite only.

## AI integration

Developer 3 implements the synchronous `PlannerService.generate(request, context)` protocol in `services/planner.py`. Inputs and outputs are Pydantic models from `schemas/planner.py`. The context is a database snapshot of unfinished tasks and unfinished goals. The backend owns database access; the service performs no database writes. Build a small adapter around the AI engine and inject it with:

```python
from backend.main import create_app
from ai_engine.adapter import LifeOSPlanner  # illustrative path; agree it with Developer 3
app = create_app(planner_service=LifeOSPlanner())
```

Then run `uvicorn your_integration_module:app`. Do not use that illustrative import until Developer 3 creates it. A synchronous provider should set its own finite network timeout. The endpoint runs in FastAPI's worker thread pool. If the engine is asynchronous, agree and revise the protocol before integration.

Until injection, `/api/planner/generate` returns HTTP 503. Adapter failures or invalid schedules return 502. Generation previews a schedule without storing it or altering tasks. Goal-to-task generation, prioritization and rescheduling belong to Developer 3; the backend does not duplicate them.

## Scope and handoff

See `API_CONTRACT.md` for payloads, responses, dates and errors. The frontend must approve the proposed field names, list format, UUID IDs and timezone policy. Developer 3 must approve the planner window, synchronous protocol, response accounting and preview-only behavior. Multi-user authentication/ownership, versioned migrations, planner persistence and deployment are subsequent MVP work. Keep this prototype on localhost until those requirements are implemented.


## Enable the existing AI engine

Developer 3's `ai-engine/` folder currently lives on `feature/ai-planner`, not on this backend branch. **Do not turn on the adapter until the team integrates that folder**. After it is available alongside `backend/`, set `ENABLE_AI_PLANNER=true` in `backend/.env` (or your shell environment) and restart Uvicorn. No additional AI API key is required for the existing deterministic scheduler. The adapter delegates to Developer 3's `generate_daily_plan` function and translates its HH:MM output to the backend's timezone-aware API contract.

When disabled (default), `/api/planner/generate` still responds 503 rather than presenting an invented schedule. The adapter relies on Developer 3 retaining `ai-engine/planner.py` and its `generate_daily_plan(tasks, available_minutes, plan_date, start_time)` interface. Confirm that interface before merging. Run `python -m pytest backend/tests -q` after integration and exercise one real planner API call.

**Integration limitations:** the existing engine only consumes minute-level windows; the adapter rounds the requested start up to the next minute and budgets whole minutes. The scheduler assumes wall-clock HH:MM; use a same-day time window without DST offset changes. Authentication, multi-user isolation, planner persistence and versioned database migrations remain outside this prototype.
