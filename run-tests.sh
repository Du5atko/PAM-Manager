#!/bin/bash
# Setup development environment and run full test suite
# Usage: ./run-tests.sh [OPTIONS]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
COVERAGE=false
VERBOSE=false
MARKERS=""
PARALLEL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -h|--help)
            echo "Usage: ./run-tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --coverage      Run tests with coverage report"
            echo "  -v, --verbose   Verbose output"
            echo "  -m, --markers   Run tests matching marker (unit, integration, etc.)"
            echo "  -p, --parallel  Run tests in parallel (requires pytest-xdist)"
            echo "  -h, --help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run-tests.sh                           # Run all tests"
            echo "  ./run-tests.sh --coverage                # With coverage report"
            echo "  ./run-tests.sh -m unit                   # Only unit tests"
            echo "  ./run-tests.sh --coverage --parallel     # Parallel with coverage"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}  PAM Manager - Test Suite Runner${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -e ".[dev]" 2>/dev/null || true

if [ "$PARALLEL" = true ]; then
    pip install -q pytest-xdist 2>/dev/null || true
fi

echo ""

# Build pytest command
PYTEST_CMD="pytest"

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=pam_manager --cov-report=html --cov-report=term-missing"
fi

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ ! -z "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m $MARKERS"
fi

if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
echo "Command: $PYTEST_CMD"
echo ""

if eval "$PYTEST_CMD"; then
    EXIT_CODE=0
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${BLUE}Coverage report:${NC}"
        echo "  HTML report: htmlcov/index.html"
        if command -v xdg-open &> /dev/null; then
            read -p "Open coverage report? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                xdg-open htmlcov/index.html
            fi
        fi
    fi
else
    EXIT_CODE=1
    echo ""
    echo -e "${YELLOW}Some tests failed. See output above.${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
exit $EXIT_CODE
