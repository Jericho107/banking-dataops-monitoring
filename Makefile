.PHONY: install test lint ci up down generate ingest quality reconcile incident dashboard reset clean

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check .

ci: lint test

up:
	docker compose up -d --wait

down:
	docker compose down

generate:
	python -m banking_dataops.generate_synthetic_data --output-dir data --customers 100 --transactions 1500 --seed 42

ingest:
	python -m banking_dataops.ingest

quality:
	python -m banking_dataops.quality_checks

reconcile:
	python -m banking_dataops.reconciliation

incident:
	python -m banking_dataops.incident_report

dashboard:
	streamlit run dashboard/streamlit_app.py

reset:
	docker compose down -v
	docker compose up -d --wait
	python -m banking_dataops.generate_synthetic_data --output-dir data --customers 100 --transactions 1500 --seed 42
	python -m banking_dataops.ingest
	python -m banking_dataops.quality_checks
	python -m banking_dataops.reconciliation

clean:
	rm -f data/*.csv
	rm -f output/*.md
