#!/bin/bash
# Script to run all checks (tests + linting + formatting)

set -e

echo "🚀 Running Full CI Pipeline..."
echo "=============================="

echo ""
echo "Step 1: Formatting code..."
./format_code.sh

echo ""
echo "Step 2: Running linting checks..."
./run_lint.sh

echo ""
echo "Step 3: Running tests..."
./run_tests.sh

echo ""
echo "=============================="
echo "🎉 All checks passed!"
