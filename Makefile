# ============================================================================
# AI Price Predictor — Developer Makefile
# Mirrors exactly what the CI pipeline runs locally (see .github/workflows/ci.yml)
# ============================================================================

.PHONY: help setup install dev-deps run test lint format security validate clean

help:  ## Show all targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: dev-deps  ## One-shot: install both runtime and dev dependencies

install:  ## Install runtime dependencies
	pip install -r requirements.txt

dev-deps:  ## Install development/CI dependencies
	pip install -r requirements-dev.txt

run:  ## Launch the Streamlit app locally
	streamlit run app.py

test:  ## Run the pytest test-suite
	python -m pytest

lint:  ## Lint with ruff (errors, style, imports)
	ruff check .

format:  ## Check formatting with ruff
	ruff format --check .

format-fix:  ## Auto-fix lint & formatting issues
	ruff check --fix .
	ruff format .

security:  ## Audit dependencies for known CVEs
	pip-audit -r requirements.txt --desc on

validate: lint format test  ## Full local equivalent of CI quality gate

clean:  ## Remove Python caches
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true