.PHONY: help install test coverage lint clean build

help:
	@echo "CloudOps - Development Commands"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run unit tests"
	@echo "  make coverage   - Run tests with coverage report"
	@echo "  make lint       - Run code linting"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make build      - Build binary with PyInstaller"
	@echo ""

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

coverage:
	pytest tests/ --cov=cloudops --cov-report=html --cov-report=term

lint:
	@echo "Running flake8..."
	@pip install flake8 2>/dev/null || true
	@flake8 cloudops/ --max-line-length=120 --ignore=E501,W503 || true

clean:
	rm -rf build/ dist/ *.spec
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build:
	./build.sh
