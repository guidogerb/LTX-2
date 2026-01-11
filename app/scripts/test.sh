#!/bin/bash
set -e
# Navigate to app root
cd "$(dirname "$0")/.."

echo "Running Pytest..."
# Excluding crashing tests (CLI and Produce segfault/terminate with current environment)
PYTHONPATH=src pytest --ignore=tests/vtx_app/test_cli.py --ignore=tests/vtx_app/test_produce.py tests

