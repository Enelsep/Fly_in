VENV_DIR = .venv
MAIN_SCRIPT = main.py
DEFAULT_MAP = maps/challenger/01_the_impossible_dream.txt

.PHONY: install run debug clean lint

$(VENV_DIR)/bin/activate:
	@echo "Creating virtual environment..."
	uv venv $(VENV_DIR)

install: $(VENV_DIR)/bin/activate
	@echo "Installing dependencies..."
	uv sync

run: install
	@echo "Running Fly in..."
	uv run python3 $(MAIN_SCRIPT) $(DEFAULT_MAP) --qwfed


debug: install
	@echo "Starting debug mode..."
	uv run python3 -m pdb $(MAIN_SCRIPT) $(DEFAULT_MAP)

clean:
	@echo "Cleaning up temporary files and caches..."
	rm -rf $(VENV_DIR)
	rm -rf build/
	rm -rf dist/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint: install
	@echo "Running standard linting..."
	uv run flake8 . --exclude $(VENV_DIR)
	uv run mypy .
