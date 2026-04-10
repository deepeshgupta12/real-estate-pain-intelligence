.PHONY: api-dev api-test web-dev

api-dev:
	cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

api-test:
	cd apps/api && source .venv/bin/activate && pytest

web-dev:
	cd apps/web && npm run dev