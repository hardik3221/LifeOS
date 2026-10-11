# LifeOS frontend

A single-file, responsive dashboard that uses the existing LifeOS FastAPI backend. No build tools, Node.js installation or frontend framework are needed. All application JavaScript and CSS live in `frontend/index.html`. Google Fonts require internet; system fonts are used if unavailable.

## Run locally

1. Start the backend following `backend/README.md` on the backend branch (or after the backend PR is merged).
2. From the repository root, serve this folder:

```bash
python3 -m http.server 5173 --directory frontend
```

3. Open http://localhost:5173
4. In **Settings**, enter `http://localhost:8000` if it differs from your backend URL.

Do not open `index.html` using `file://`; use the local server so the browser has a supported origin.

## API contract

The frontend relies on:
- `GET /api/tasks`, `POST /api/tasks`, `PATCH /api/tasks/{id}`, `DELETE /api/tasks/{id}`
- `GET /api/goals`, `POST /api/goals`, `PATCH /api/goals/{id}`, `DELETE /api/goals/{id}`
- `POST /api/planner/generate`

Requests follow `backend/API_CONTRACT.md`. It expects **bare JSON arrays** from the list endpoints, UUID IDs, 204 responses for deletion, and JSON errors with `error.message`. Planner requests use the selected local date with explicit time-zone offsets. The planner only works after Developer 3's AI engine is integrated with the backend and `ENABLE_AI_PLANNER=true`.

The local development backend permits `http://localhost:5173` through CORS by default. Change the backend's CORS settings for another host or deployment. A backend deployed over HTTPS is required for a deployed HTTPS frontend.

## Scope and limitations

- No authentication or user isolation; only run this prototype in a trusted local environment.
- Tasks and goals are persisted by the backend, not the browser. Only the API URL is saved in localStorage.
- Lists request at most 500 items per resource; pagination/load-more is future work.
- Planning creates a preview, not a persistent calendar. The AI engine is not bundled in this branch.
- Check backend and browser console on any connection failure; the app displays a user-friendly error.
