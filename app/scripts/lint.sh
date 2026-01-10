#!/bin/bash
set -e
# Navigate to app root
cd "$(dirname "$0")/.."

echo "Checking Black..."
black --check src tests --preview

echo "Checking isort..."
isort --check-only src tests

echo "Running Flake8..."
# create setup.cfg or use default if not present
if [ -f "setup.cfg" ]; then
    flake8 src tests
else
    # default ignore some common issues if config missing
    flake8 src tests --max-line-length=120 --ignore=E203,W503
fi

echo "Running Mypy..."
mypy src tests --ignore-missing-imports
