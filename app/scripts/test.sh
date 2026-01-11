#!/bin/bash
set -e
# Navigate to app root
cd "$(dirname "$0")/.."

echo "Running Pytest..."
# Excluding crashing tests (Produce segfaults/terminates with current environment)
PYTHONPATH=src pytest --cov=vtx_app --cov-report=term-missing --ignore=tests/vtx_app/test_produce.py tests

