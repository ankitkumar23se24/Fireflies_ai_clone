.PHONY: install migrate seed reseed backend frontend test test-backend test-frontend docker lint

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

migrate:
	cd backend && python -m alembic upgrade head

seed:
	cd backend && python -m app.seed.seed

reseed:
	cd backend && python -m app.seed.seed --reset

backend: migrate seed
	cd backend && python -m uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest -q

test-frontend:
	cd frontend && npm test

lint:
	cd frontend && npm run typecheck

docker:
	docker compose up --build
