#!/bin/bash
set -e
# Navigate to app root
cd "$(dirname "$0")/.."

echo "Running Black..."
black src tests --preview

echo "Running isort..."
isort src tests
