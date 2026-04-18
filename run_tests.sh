#!/bin/bash
# Script to run tests locally with coverage

set -e

echo "🧪 Running Poetry Bot Tests..."
echo "================================"

# Check if test requirements are installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing test dependencies..."
    pip install -r requirements-test.txt
fi

# Run pytest with coverage
echo ""
echo "Running pytest with coverage report..."
pytest tests/ \
    --cov=app \
    --cov=bot \
    --cov-report=html \
    --cov-report=term-missing \
    -v

# Show coverage summary
echo ""
echo "================================"
echo "✅ Tests complete!"
echo "📊 Coverage report generated in htmlcov/index.html"
echo ""
echo "To view the report, run:"
echo "  open htmlcov/index.html  (macOS)"
echo "  start htmlcov/index.html (Windows)"
echo "  xdg-open htmlcov/index.html (Linux)"
