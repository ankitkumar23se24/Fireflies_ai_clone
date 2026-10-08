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

