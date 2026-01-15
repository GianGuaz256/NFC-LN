# Makefile for LN-NFC project

.PHONY: help install test lint format clean docker-build docker-up docker-down docker-logs setup

help:
	@echo "LN-NFC Development Commands"
	@echo ""
	@echo "  make install       Install Python dependencies"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-hw       Run hardware tests"
	@echo "  make lint          Run linters"
	@echo "  make format        Format code"
	@echo "  make clean         Clean build artifacts"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-up     Start Docker services"
	@echo "  make docker-down   Stop Docker services"
	@echo "  make docker-logs   View Docker logs"
	@echo "  make setup         Run Raspberry Pi setup script"

install:
	pip3 install -r requirements.txt

test:
	pytest -v

test-unit:
	pytest -v -m "not hardware and not integration and not e2e"

test-hw:
	pytest -v -m hardware

test-integration:
	pytest -v -m integration

test-e2e:
	pytest -v -m e2e

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term

lint:
	@echo "Running linters..."
	@python3 -m flake8 src/ cli.py || true
	@python3 -m pylint src/ cli.py || true

format:
	@echo "Formatting code..."
	@python3 -m black src/ cli.py tests/ || true
	@python3 -m isort src/ cli.py tests/ || true

clean:
	@echo "Cleaning build artifacts..."
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/*/__pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-restart:
	docker compose restart

setup:
	@echo "Running Raspberry Pi setup script..."
	@chmod +x setup-pi.sh
	@sudo ./setup-pi.sh

# Development shortcuts
dev: install
	@echo "Development environment ready!"

run-daemon:
	python3 cli.py daemon

run-status:
	python3 cli.py status

# Create necessary directories
dirs:
	mkdir -p logs
	mkdir -p data
