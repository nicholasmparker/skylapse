PY = python3
VENV = .venv
PIP = $(VENV)/bin/pip
PYBIN = $(VENV)/bin/python

.PHONY: venv install dev lint fmt typecheck test run

venv:
	$(PY) -m venv $(VENV)

install: venv
	$(PIP) install -U pip
	$(PIP) install -e .

dev: venv
	$(PIP) install -U pip
	$(PIP) install -e .[dev]

lint:
	$(VENV)/bin/ruff check .

fmt:
	$(VENV)/bin/black .
	$(VENV)/bin/ruff check . --fix

typecheck:
	$(VENV)/bin/mypy src

test:
	$(VENV)/bin/pytest

run:
	ENV_FILE_ARG=
	if [ -f .env ]; then ENV_FILE_ARG="--env-file .env"; fi; \
	$(PYBIN) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 $$ENV_FILE_ARG
