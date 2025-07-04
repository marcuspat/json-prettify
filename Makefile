.PHONY: help install test lint format typecheck coverage clean build

help:  ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install dependencies with Poetry
	poetry install

test:  ## Run all tests
	poetry run pytest -v

test-watch:  ## Run tests in watch mode
	poetry run pytest-watch

lint:  ## Run linting with ruff
	poetry run ruff check src/json_prettify tests

format:  ## Format code with black
	poetry run black src/json_prettify tests

format-check:  ## Check code formatting without changing files
	poetry run black --check src/json_prettify tests

typecheck:  ## Run type checking with mypy
	poetry run mypy src/json_prettify

coverage:  ## Run tests with coverage report
	poetry run pytest --cov=json_prettify --cov-report=html --cov-report=term-missing

clean:  ## Clean build artifacts and cache files
	rm -rf build dist *.egg-info
	rm -rf .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	poetry build

check: lint format-check typecheck test  ## Run all checks (lint, format, typecheck, test)

pre-commit: format lint typecheck test  ## Run all pre-commit checks

dev:  ## Run development server (if applicable)
	@echo "No development server configured for this CLI tool"

docs:  ## Build documentation (if applicable)
	@echo "No documentation build configured yet"