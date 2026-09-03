#!/usr/bin/env bash
# Run Playwright E2E tests against the live admin panel.
# Usage:
#   ./tests/e2e/run.sh              # all tests
#   ./tests/e2e/run.sh test_login.py # single file
#   ./tests/e2e/run.sh -k "test_dashboard" # by keyword

set -euo pipefail
cd "$(dirname "$0")/../.."

FILE="${1:-tests/e2e/}"

echo "=== Andes Padel — Playwright E2E Tests ==="
echo "Target: https://andespadel.yachaq.io"
echo "Tests:  $FILE"
echo ""

python -m pytest "$FILE" \
    -c tests/e2e/pytest.ini \
    -m e2e \
    --tb=short \
    -v \
    --timeout=30 \
    "$@"
