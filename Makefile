.PHONY: setup up seed test eval down lint
setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'
up:
	docker compose up --build -d
seed:
	docker compose exec api python -m database.seed --orders 50000
test:
	docker compose run --rm api pytest -q
eval:
	docker compose exec api python -m evaluation.run --output evaluation/results.json
lint:
	docker compose run --rm api sh -c 'ruff check . && mypy backend agents database'
down:
	docker compose down -v
