.PHONY: help install install-dev test lint format clean run build security

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests with coverage
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

test-integration: ## Run integration tests (requires network access)
	RUN_ARCGIS_INTEGRATION=1 pytest tests/ -v -m integration

test-watch: ## Run tests in watch mode
	pytest-watch tests/

lint: ## Run linters (flake8, pylint, mypy)
	@echo "Running flake8..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
	@echo "Running pylint..."
	pylint arcgis_client.py session_manager.py compliance_checker.py config.py logger.py errors.py || true
	@echo "Running mypy..."
	mypy . --ignore-missing-imports || true

format: ## Format code with black and isort
	@echo "Running black..."
	black . --line-length=100
	@echo "Running isort..."
	isort . --profile black

format-check: ## Check code formatting without making changes
	black . --check --line-length=100
	isort . --check-only --profile black

security: ## Run security checks
	@echo "Running bandit..."
	bandit -r . -x tests,examples,.venv
	@echo "Running safety..."
	safety check --json || true

clean: ## Clean build artifacts and caches
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*.log' -delete
	find . -type f -name '*.tmp' -delete

run: ## Run the main application
	python main.py

run-example: ## Run usage examples
	python examples/usage_examples.py

build: clean ## Build distribution packages
	python -m build

check-all: format-check lint security test ## Run all checks (format, lint, security, test)

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

setup-env: ## Create .env file from template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created from template. Please update with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi

docker-build: ## Build Docker image
	docker build -t arcgis-client:latest .

docker-run: ## Run Docker container
	docker run --rm -it arcgis-client:latest

init: install-dev setup-env ## Initialize development environment
	@echo "Development environment initialized!"
	@echo "Please update .env file with your configuration."

update-deps: ## Update dependencies to latest versions
	pip install --upgrade pip setuptools wheel
	pip install --upgrade -r requirements.txt

freeze-deps: ## Freeze current dependencies
	pip freeze > requirements-lock.txt

coverage-report: test ## Generate and open HTML coverage report
	@echo "Opening coverage report..."
	@open htmlcov/index.html || xdg-open htmlcov/index.html || start htmlcov/index.html

docs: ## Generate documentation
	@echo "Generating documentation..."
	@echo "Documentation generation not yet implemented"

# Development helpers
.PHONY: watch
watch: ## Watch for file changes and run tests
	pytest-watch

.PHONY: shell
shell: ## Start Python shell with project context
	python -i -c "from arcgis_client import *; from session_manager import *; from compliance_checker import *"
