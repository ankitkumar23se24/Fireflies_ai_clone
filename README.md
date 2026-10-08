# Meeting Intelligence Platform

A Fireflies-inspired meeting intelligence workspace built with a FastAPI backend and a polished Next.js dashboard.

## Features

- Meeting library and dashboard overview
- Meeting detail pages with transcript, summary, action items, and AI-style Q&A
- Global search across meetings, summaries, and transcript text
- Import transcript text or upload `.txt`, `.vtt`, and `.json` transcripts
- Action item management and meeting metadata updates
- Dark-mode-friendly SaaS-inspired UI

## Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, Lucide
- Backend: FastAPI, SQLAlchemy, SQLite
- Testing: Pytest for backend

## Local development

```bash
# Backend
cd backend
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m app.seed.seed
python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in the browser.

## Environment

Use `.env.example` as the template for local environment variables.

## Testing

```bash
cd backend
python -m pytest -q
cd ../frontend
npm test
npm run typecheck
npm run build
```

Run frontend validation sequentially: `npm test`, then `npm run typecheck`, then `npm run build`. The Next.js development server and production build both use `.next`; do not run them concurrently.

## Docker

```bash
docker compose up --build
```

Compose runs the backend migrations and seeds demo meetings before serving the API. The frontend image is built as a standalone Next.js production server.

## Deploy to Render

The `render.yaml` Blueprint configures the FastAPI API and Next.js frontend as separate Render web services. The API uses SQLite on a persistent disk, so it requires the Starter plan; the frontend is configured on the Free plan.

1. Push `render.yaml` to the GitHub branch you want to deploy.
2. In Render, choose **New** → **Blueprint**.
3. Connect the GitHub repository and select that branch.
4. Review the two services and click **Apply**.
5. When prompted, provide `GEMINI_API_KEY`, or leave it blank to use the built-in heuristic AI.
6. Wait for both services to deploy and for the API health check to pass, then open `https://meeting-intelligence-web.onrender.com`.

The Blueprint uses fixed service names and corresponding `.onrender.com` URLs. If Render assigns different URLs because those names are already taken, update `FRONTEND_URL` on the API service and `NEXT_PUBLIC_API_URL` on the frontend service with the actual URLs. The frontend API URL must end with `/api/v1`; redeploy the frontend after changing it because it is embedded at build time.

The API disk is mounted at `/var/data`. Database migrations and demo seeding run at API startup; seeding does not reset an existing database.
