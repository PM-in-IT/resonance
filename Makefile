.PHONY: dev down migrate test lint format

dev:
	docker compose up --build

down:
	docker compose down

migrate:
	alembic upgrade head

test:
	pytest

lint:
	ruff check .
	mypy app

format:
	ruff format .
	ruff check --fix .

worker:
	.venv/bin/rq worker \
		-w rq.worker.SpawnWorker \
		media \
		--url redis://localhost:6379/0
