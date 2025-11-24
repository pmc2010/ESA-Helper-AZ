#!/bin/bash

# Run tests with coverage reports
# Usage: ./scripts/test_coverage.sh

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       Running Tests with Coverage Reports                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Python coverage
echo "Python Coverage Report:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v pytest &> /dev/null; then
    pytest --cov=app --cov-report=term-missing --cov-report=html
else
    python3 -m pytest --cov=app --cov-report=term-missing --cov-report=html
fi

echo ""
echo "✓ Python coverage report generated in htmlcov/index.html"

# JavaScript coverage
echo ""
echo "JavaScript Coverage Report:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "node_modules" ]; then
    echo "Installing JavaScript dependencies..."
    npm install
fi

npm run test:coverage

echo ""
echo "✓ JavaScript coverage generated"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       Coverage reports ready for review                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
