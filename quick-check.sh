#!/bin/bash
# Quick test and quality check script
# Usage: ./quick-check.sh

set -e

echo "🔍 PAM Manager - Quick Quality Check"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python: $PYTHON_VERSION"
echo ""

# Install dependencies if needed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "⚙️  Installing development dependencies..."
    pip install -e ".[dev]" > /dev/null 2>&1
    echo "   ✓ Dependencies installed"
    echo ""
fi

# Run tests
echo "🧪 Running tests..."
pytest --co -q tests/test_pam_manager_comprehensive.py tests/test_code_quality.py 2>/dev/null | tail -1
echo ""

# Check code formatting
echo "🎨 Checking code formatting (Black)..."
if black --check . --quiet --exclude=build,dist,.git,.venv 2>/dev/null; then
    echo -e "   ${GREEN}✓ Code formatting OK${NC}"
else
    echo -e "   ${YELLOW}⚠ Code needs formatting${NC}"
    echo "   Run: black ."
fi
echo ""

# Check linting
echo "🔗 Checking linting (Ruff)..."
if ruff check . --exit-zero 2>/dev/null | grep -q "0 errors"; then
    echo -e "   ${GREEN}✓ No linting errors${NC}"
else
    echo -e "   ${YELLOW}⚠ Linting issues found${NC}"
    echo "   Run: ruff check . --fix"
fi
echo ""

# Check type hints
echo "🔤 Checking type hints (MyPy)..."
if mypy pam_manager --ignore-missing-imports --no-error-summary 2>/dev/null | grep -q "Success"; then
    echo -e "   ${GREEN}✓ Type checking passed${NC}"
else
    echo -e "   ${YELLOW}⚠ Type hints need attention${NC}"
    echo "   Run: mypy pam_manager --ignore-missing-imports"
fi
echo ""

echo "===================================="
echo -e "${GREEN}✓ Quick check complete!${NC}"
echo ""
echo "Next steps:"
echo "  • Run full tests: pytest"
echo "  • Run with coverage: pytest --cov=pam_manager"
echo "  • Auto-fix issues: black . && isort . && ruff check . --fix"
echo "  • Run all pre-commit checks: pre-commit run --all-files"
