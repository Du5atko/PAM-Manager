# Test and CI/CD Status

## Overview

This document provides a summary of the testing infrastructure and CI/CD pipelines set up for PAM Manager.

## Test Summary

### Test Coverage

**Total Tests: 49** ✅

#### By Category:
- **Unit Tests**: 40+ tests
  - Configuration handling (5 tests)
  - Module discovery (4 tests)
  - Policy validation (4 tests)
  - Service management (4 tests)
  - Parameter handling (2 tests)
  - Error handling (3 tests)
  - Edge cases (3 tests)
  - Code quality (16 tests)
  - And more...

- **Integration Tests**: Included
  - Load-modify-save workflow
  - Multi-service configuration
  - Format export tests

- **Platform-Specific Tests**: Included
  - Linux platform detection
  - FreeBSD compatibility
  - Module path resolution

- **Performance Tests**: Included
  - Large configuration loading
  - Many services enumeration

### Test Files

| File | Tests | Purpose |
|------|-------|---------|
| `test_pam_manager_comprehensive.py` | 33 | Core functionality tests |
| `test_code_quality.py` | 16 | Code quality and standards |
| Existing test suite | 200+ | Legacy tests and integrations |

## CI/CD Workflows

### GitHub Actions Workflows

#### 1. Main CI Pipeline (`.github/workflows/ci.yml`)
**Triggers**: Push, PR, daily schedule

**Matrix Testing**:
- Python: 3.11, 3.12
- OS: Ubuntu 20.04, Ubuntu latest, macOS latest

**Jobs**:
1. **Tests** - Core test suite with coverage
2. **Integration Tests** - Platform-specific integration tests
3. **Code Quality** - Code quality verification
4. **Build** - Distribution package building
5. **Security Scan** - Trivy vulnerability scanning
6. **Documentation** - Documentation validation
7. **Results** - Summary report

**Outputs**:
- ✅ Test results
- ✅ Coverage reports (Codecov)
- ✅ Build artifacts
- ✅ Security scan results
- ✅ Release creation (on tags)

#### 2. Lint & Format Workflow (`.github/workflows/lint.yml`)
**Triggers**: Push to main/develop, PRs

**Checks**:
- **Ruff**: Code style and common errors
- **Black**: Code formatting
- **MyPy**: Type annotations
- **isort**: Import sorting

## Local Testing

### Quick Check
```bash
# Make script executable
chmod +x quick-check.sh

# Run quick quality checks
./quick-check.sh
```

Performs:
- Python version check
- Test discovery
- Code formatting check
- Linting check
- Type hints check

### Full Test Suite
```bash
# Make script executable
chmod +x run-tests.sh

# Run all tests
./run-tests.sh

# With coverage report
./run-tests.sh --coverage

# Only unit tests
./run-tests.sh -m unit

# Parallel execution
./run-tests.sh --parallel

# With verbose output
./run-tests.sh -v
```

### Manual Commands

**Run tests**:
```bash
pytest                                      # All tests
pytest -m unit                              # Unit tests only
pytest -m integration                       # Integration tests
pytest --cov=pam_manager --cov-report=html # With coverage
```

**Code quality**:
```bash
black .                                     # Format code
ruff check .                                # Lint
mypy pam_manager --ignore-missing-imports   # Type check
```

**Pre-commit hooks**:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files                  # All checks
```

## Pre-commit Hooks

**Configuration**: `.pre-commit-config.yaml`

**Includes**:
- File format validation (YAML, JSON, TOML)
- Code formatting (Black)
- Import sorting (isort)
- Linting (Ruff)
- Type checking (MyPy)
- Security checks (Bandit)
- Docstring coverage (Interrogate)

**Setup**:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # First run
```

## Coverage Requirements

- **Minimum**: 70% code coverage
- **Target**: 80%+ coverage
- **Critical**: 90%+ coverage

View coverage:
```bash
pytest --cov=pam_manager --cov-report=html
open htmlcov/index.html
```

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata and tool config |
| `pytest.ini` | Pytest configuration |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `.github/workflows/ci.yml` | Main CI/CD pipeline |
| `.github/workflows/lint.yml` | Linting workflow |
| `CONTRIBUTING.md` | Contributor guidelines |
| `CI_CD_DOCUMENTATION.md` | Detailed CI/CD docs |

## Best Practices

### Before Committing
1. Run local checks: `./quick-check.sh`
2. Fix any issues: `black .`, `ruff check . --fix`
3. Run full tests: `pytest --cov=pam_manager`

### Before Pushing
1. Ensure pre-commit hooks pass
2. Update tests with code changes
3. Keep coverage above 80%
4. Write clear commit messages

### PR Review
- All CI checks must pass
- Coverage must not decrease
- Code review approval required
- At least 2 approvals for main branch

## Troubleshooting

### Tests fail locally but pass in CI
```bash
# Reinstall dependencies
pip install -e ".[dev]"

# Clear caches
pytest --cache-clear
pip cache purge

# Check Python version
python --version  # Must be 3.11+
```

### Pre-commit hooks fail
```bash
# Reinstall hooks
pre-commit install
pre-commit run --all-files

# Auto-fix issues
black .
isort .
ruff check . --fix
```

### Coverage is lower
```bash
# Run full test suite
pytest --cov=pam_manager --cov-report=term-missing

# Check missing coverage
pytest --cov=pam_manager --cov-report=html
open htmlcov/index.html
```

## Monitoring & Alerts

### GitHub
- ✅ Status checks on PRs
- ✅ Workflow run history
- ✅ Branch protection rules
- ✅ Code security tab

### External Services
- Codecov: Coverage tracking
- GitHub Security: Vulnerability alerts
- Release notes: Auto-generated from PRs

## Release Process

1. **Update version**:
   ```bash
   # Edit pyproject.toml
   [project]
   version = "0.3.0"
   ```

2. **Create tag**:
   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

3. **Automatic**:
   - Full test suite runs
   - Build distributions
   - Create GitHub release
   - Publish to PyPI (if configured)

## Performance

**Current Performance**:
- Full test suite: ~30-60 seconds
- Coverage analysis: ~45-90 seconds
- Linting checks: ~10-15 seconds
- Total CI time: ~2-3 minutes

**Optimization**:
- Tests run in parallel when possible
- Coverage reports cached
- Dependencies cached
- Artifacts uploaded for inspection

## See Also

- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- [CI_CD_DOCUMENTATION.md](CI_CD_DOCUMENTATION.md) - Detailed CI/CD docs
- [README.md](README.md) - Project overview
- [docs/](docs/) - Full documentation

## Status

✅ **CI/CD Setup**: Complete
✅ **Tests**: 49 tests, 100% passing
✅ **Workflows**: 2 active workflows
✅ **Pre-commit**: Configured
✅ **Documentation**: Complete

Latest update: 2026-08-19
