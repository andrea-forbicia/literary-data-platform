# Developer commands. Every target runs tools through uv, so they use the
# versions pinned in uv.lock. Recipes must be indented with a tab.

.PHONY: setup lint format test

## Create .venv from uv.lock and install the git pre-commit hook.
setup:
	uv sync --locked
	uv run pre-commit install

## Check lint and formatting without changing files (what CI runs).
lint:
	uv run ruff check .
	uv run ruff format --check .

## Fix what ruff can fix automatically and reformat the code.
format:
	uv run ruff check --fix .
	uv run ruff format .

## Run the whole pytest suite.
test:
	uv run pytest
