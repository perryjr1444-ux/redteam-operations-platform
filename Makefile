.PHONY: help install dev test lint format clean run docker-build docker-run migrate

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Red Team Exercise Manager - Available Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e .

test: ## Run tests with coverage
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	pytest tests/ -v

lint: ## Run linting checks
	flake8 app/ tests/
	mypy app/ --ignore-missing-imports
	black --check app/ tests/

format: ## Format code with black and isort
	black app/ tests/
	isort app/ tests/

security: ## Run security checks
	bandit -r app/ -ll
	safety check

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf dist/ build/

run: ## Run the application locally
	uvicorn app.main:app --host 0.0.0.0 --port 5172 --reload

run-prod: ## Run the application in production mode
	uvicorn app.main:app --host 0.0.0.0 --port 5172 --workers 4

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration (use MSG="migration message")
	alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history

docker-build: ## Build Docker image
	docker build -f Containerfile -t redteam-app:latest .

docker-run: ## Run Docker container
	docker run -d -p 5172:5172 --name redteam-app redteam-app:latest

docker-stop: ## Stop Docker container
	docker stop redteam-app && docker rm redteam-app

compose-up: ## Start with docker-compose
	docker-compose up -d

compose-down: ## Stop docker-compose services
	docker-compose down

compose-logs: ## Show docker-compose logs
	docker-compose logs -f

compose-build: ## Build with docker-compose
	docker-compose build

init-db: ## Initialize database and populate initial data
	mkdir -p db
	alembic upgrade head

reset-db: ## Reset database (WARNING: deletes all data)
	rm -f db/redteam.db
	alembic upgrade head

shell: ## Open Python shell with app context
	python -c "from app.main import *; from app import models, crud; import IPython; IPython.embed()"

check-all: lint test security ## Run all checks (lint, test, security)

deploy-check: ## Verify deployment readiness
	@echo "Checking deployment requirements..."
	@python -c "from app.config import settings; print(f'✓ Config loaded: {settings.APP_NAME}')"
	@echo "✓ Database directory exists" && test -d db || (mkdir -p db && echo "✓ Created db directory")
	@echo "✓ Static files exist" && test -d static || echo "✗ Missing static directory"
	@echo "✓ Templates exist" && test -d templates || echo "✗ Missing templates directory"
	@echo "✓ Schema file exists" && test -f cli_schema.yaml || echo "⚠ Missing cli_schema.yaml"
