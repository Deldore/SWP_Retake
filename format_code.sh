#!/bin/bash
# Script to format code automatically

set -e

echo "🎨 Formatting Code..."
echo "===================="

# Check if formatting tools are installed
if ! python -c "import black" 2>/dev/null; then
    echo "📦 Installing formatting tools..."
    pip install black isort
fi

echo ""
echo "Formatting with black..."
black app bot tests

echo ""
echo "Organizing imports with isort..."
isort app bot tests

echo ""
echo "===================="
echo "✅ Code formatted!"
