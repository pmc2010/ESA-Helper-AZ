#!/bin/bash

# Run all tests (Python and JavaScript)
# Usage: ./scripts/run_all_tests.sh

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          ESA Helpers - Running All Tests                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python version: $(python3 --version)"

# Check Node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

echo "✓ Node version: $(node --version)"
echo ""

# Run Python tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Running Python Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v pytest &> /dev/null; then
    pytest --tb=short
else
    echo "⚠️  pytest not found, trying with python -m pytest"
    python3 -m pytest --tb=short
fi

PYTHON_EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Running JavaScript Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "node_modules" ]; then
    echo "Installing JavaScript dependencies..."
    npm install
fi

npm test -- --passWithNoTests 2>/dev/null || npm test

JS_EXIT_CODE=$?

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    Test Results Summary                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

if [ $PYTHON_EXIT_CODE -eq 0 ]; then
    echo "✓ Python tests: PASSED"
else
    echo "✗ Python tests: FAILED"
fi

if [ $JS_EXIT_CODE -eq 0 ]; then
    echo "✓ JavaScript tests: PASSED"
else
    echo "✗ JavaScript tests: FAILED"
fi

echo ""

if [ $PYTHON_EXIT_CODE -eq 0 ] && [ $JS_EXIT_CODE -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
