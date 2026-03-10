.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync --all-extras
	@uv run pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Checking for critical linting issues: Running ruff check"
	@uv run ruff check src tests
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run --all-files
	@echo "🚀 Static type checking: Running mypy"
	@uv run mypy
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@uv run deptry .

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest with parallel execution"
	@uv run python -m pytest -x --ff -n auto --dist loadscope

.PHONY: cov
cov: ## Generate HTML coverage report
	@echo "🚀 Generating HTML coverage report"
	@uv run python -m pytest --cov --cov-config=pyproject.toml --cov-report=html

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: publish
publish: build ## Publish a release to PyPI.
	@echo "🚀 Publishing."
	@uvx twine upload -r pypi dist/*

.PHONY: docs
docs: ## Build and serve the documentation (Nextra)
	@cd apps/docs && npm run dev

.PHONY: web
web: ## Build and serve the landing page
	@cd apps/web && npm run dev

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help

.PHONY: inspector
inspector:
	@echo "🚀 Starting MCP Inspector"
	npx @modelcontextprotocol/inspector uv run --with . czechmedmcp run

.PHONY: pbdiff
pbdiff: ## Copy git diff to clipboard
	@git diff -- . ':(exclude)uv.lock' | pbcopy
