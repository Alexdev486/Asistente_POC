.PHONY: db-up db-down db-migrate db-seed db-ingest-chunks embeddings-worker api-install api-run web-install web-run

db-up:
	docker compose -f infra/docker/docker-compose.yml up -d

db-down:
	docker compose -f infra/docker/docker-compose.yml down

db-migrate:
	DATABASE_URL=postgresql://postgres:postgres@localhost:5432/asistente_poc bash scripts/db/apply_migrations.sh

db-seed:
	DATABASE_URL=postgresql://postgres:postgres@localhost:5432/asistente_poc bash scripts/db/seed.sh

db-ingest-chunks:
	DATABASE_URL=postgresql://postgres:postgres@localhost:5432/asistente_poc bash scripts/db/ingest_knowledge_chunks.sh

embeddings-worker:
	DATABASE_URL=postgresql://postgres:postgres@localhost:5432/asistente_poc bash scripts/dev/run_embedding_worker.sh

api-install:
	pip install -r apps/api/requirements.txt

api-run:
	bash scripts/dev/run_api.sh

web-install:
	cd apps/web && npm install

web-run:
	bash scripts/dev/run_web.sh
