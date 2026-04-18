#!/bin/bash
# Script to run linting and formatting checks

set -e

echo "🔍 Running Linting & Formatting Checks..."
echo "=========================================="

# Check if linting tools are installed
if ! python -c "import black" 2>/dev/null; then
    echo "📦 Installing linting tools..."
    pip install black flake8 isort pylint
fi

echo ""
echo "1️⃣  Checking imports with isort..."
isort --check-only --diff app bot tests || true

echo ""
echo "2️⃣  Checking format with black..."
black --check app bot tests || true

echo ""
echo "3️⃣  Linting with flake8..."
flake8 app bot tests --max-line-length=127 --statistics || true

echo ""
echo "=========================================="
echo "✅ Linting check complete!"
echo ""
echo "To automatically fix issues, run:"
echo "  black app bot tests"
echo "  isort app bot tests"
