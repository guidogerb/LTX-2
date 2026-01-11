#!/bin/bash
set -e
# Navigate to app root
cd "$(dirname "$0")/.."

echo "Running Pytest..."
PYTHONPATH=src pytest --cov=vtx_app --cov-report=term-missing tests
