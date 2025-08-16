.PHONY: format lint test

format:
	ruff format $(FORMAT_ARGS) .

lint:
	ruff check .

test:
	pytest $(PYTEST_ADDOPTS)

