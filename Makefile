.PHONY: help install dev-install clean run-capture run-scan run-repeat run-live test lint format

# Default target
help:
	@echo "RF Sniffer - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install dependencies with uv (macOS/development)"
	@echo "  dev-install  Install development dependencies"
	@echo "  rpi-install  Install Raspberry Pi dependencies"
	@echo "  rpi-dev-install  Install RPi + dev dependencies"
	@echo "  clean        Clean virtual environment and cache"
	@echo ""
	@echo "Running:"
	@echo "  run-capture  Run capture mode (default: 60s, channel 76)"
	@echo "  run-scan     Run channel scan mode (default: 60s)"
	@echo "  run-repeat   Run repeat mode (requires FILE=path)"
	@echo "  run-live     Run live repeat mode (default: 60s, channel 76)"
	@echo ""
	@echo "Development:"
	@echo "  test         Run tests"
	@echo "  lint         Run linter"
	@echo "  format       Format code"
	@echo ""
	@echo "Examples:"
	@echo "  make run-scan DURATION=120"
	@echo "  make run-capture CHANNEL=50 DURATION=30 FILE=capture.txt"
	@echo "  make run-repeat FILE=capture.txt CHANNEL=76"

# Setup commands
install:
	uv sync

dev-install:
	uv sync --dev

rpi-install:
	uv sync --extra rpi

rpi-dev-install:
	uv sync --extra rpi --dev

clean:
	uv venv --clear
	rm -rf .venv
	rm -rf __pycache__
	rm -f *.pyc
	rm -f *.txt

# Run commands
run-capture:
	uv run python main.py capture -d $(or $(DURATION),60) -c $(or $(CHANNEL),76) -f $(or $(FILE),capture_$(shell date +%s).txt)

run-scan:
	uv run python main.py scan -d $(or $(DURATION),60) -f $(or $(FILE),scan_$(shell date +%s).txt)

run-repeat:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter required for repeat mode"; \
		echo "Usage: make run-repeat FILE=capture.txt"; \
		exit 1; \
	fi
	uv run python main.py repeat -f $(FILE) -c $(or $(CHANNEL),76) -d $(or $(DELAY),0.1)

run-live:
	uv run python main.py live -d $(or $(DURATION),60) -c $(or $(CHANNEL),76) -d $(or $(DELAY),0.1)

# Development commands
test:
	uv run python -m pytest tests/ -v

lint:
	uv run python -m flake8 *.py
	uv run python -m black --check *.py

format:
	uv run python -m black *.py
	uv run python -m isort *.py

# Quick setup for new environment
setup: install
	@echo "Virtual environment setup complete!"
	@echo "Run 'make help' to see available commands"
