#!/bin/bash

# Run only file requirement tests
# Usage: ./scripts/test_file_requirements.sh

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Running File Requirement Tests (Most Critical)       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "These tests verify the Direct Pay file requirements are correct:"
echo "  ✓ Invoice required for Direct Pay"
echo "  ✓ Receipt NOT required for Direct Pay"
echo "  ✓ Curriculum optional except for Supplemental Materials"
echo "  ✓ Attestation never required for Direct Pay"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Running Python File Requirement Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v pytest &> /dev/null; then
    pytest tests/test_file_requirements.py -v
else
    python3 -m pytest tests/test_file_requirements.py -v
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Running JavaScript File Requirement Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "node_modules" ]; then
    echo "Installing JavaScript dependencies..."
    npm install --silent
fi

npm test -- --testNamePattern="File Requirements|Direct Pay" --verbose 2>/dev/null || \
npm test -- --testNamePattern="File Requirements|Direct Pay"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  File requirement tests complete                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
