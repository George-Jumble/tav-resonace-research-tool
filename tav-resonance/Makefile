.PHONY: help install install-dev build test lint format typecheck docs clean upload-testpypi upload-pypi

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)
PIP ?= $(shell if [ -x .venv/bin/pip ]; then echo .venv/bin/pip; else echo pip3; fi)

help:
	@echo "tav-resonance development targets"
	@echo ""
	@echo "  make install-dev   Install editable package with dev + examples extras"
	@echo "  make build         Build sdist and wheel (dist/)"
	@echo "  make test          Run pytest with coverage"
	@echo "  make lint          Ruff lint and format check"
	@echo "  make format        Auto-format with ruff"
	@echo "  make typecheck     Run mypy on src/"
	@echo "  make docs          Render example notebooks to docs/_build/"
	@echo "  make clean         Remove build artifacts and caches"
	@echo "  make upload-testpypi  Upload dist/ to TestPyPI (requires TWINE credentials)"
	@echo "  make upload-pypi      Upload dist/ to PyPI (requires TWINE credentials)"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev,examples]"

build:
	$(PYTHON) -m build

test:
	pytest --cov=tav_resonance --cov-report=term-missing

lint:
	ruff check src tests
	ruff format --check src tests

format:
	ruff format src tests
	ruff check --fix src tests

typecheck:
	mypy src

docs:
	mkdir -p docs/_build
	jupyter nbconvert --to html --output-dir docs/_build examples/*.ipynb
	@echo "HTML notebooks written to docs/_build/"

clean:
	rm -rf dist build docs/_build .pytest_cache .coverage htmlcov
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -prune -exec rm -rf {} +

upload-testpypi: build
	twine upload --repository testpypi dist/*

upload-pypi: build
	twine upload dist/*