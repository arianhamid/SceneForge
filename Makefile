PYTHON ?= python

.PHONY: help install format lint typecheck test coverage check

help:
	@echo "SceneForge development commands"
	@echo "  make install    Install editable package and development tools"
	@echo "  make format     Apply Ruff fixes and formatting"
	@echo "  make lint       Check lint and formatting"
	@echo "  make typecheck  Run strict type checking"
	@echo "  make test       Run the complete test suite"
	@echo "  make coverage   Enforce the instrumented 80% coverage gate"
	@echo "  make check      Run all non-mutating quality gates"

install:
	$(PYTHON) -m pip install -e ".[dev]"

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

typecheck:
	$(PYTHON) -m mypy --strict sceneforge

test:
	$(PYTHON) -m pytest -q

coverage:
	$(PYTHON) -m pytest -q --cov=sceneforge \
		--cov-report=xml --cov-report=term-missing \
		--cov-fail-under=80

check: lint typecheck test
