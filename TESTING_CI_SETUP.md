# PAM Manager - Testing & CI/CD Setup Guide

## 🎯 What's Been Set Up

Complete testing infrastructure and GitHub Actions CI/CD pipeline for PAM Manager project.

### ✅ Components Installed

#### 1. **Test Suite** (49 new tests)
- **Comprehensive Tests**: `tests/test_pam_manager_comprehensive.py` (33 tests)
  - Configuration handling
  - PAM module discovery
  - Policy validation
  - Service management
  - Integration workflows
  - Platform-specific testing
  - Performance tests
  - Error handling
  - Edge cases

- **Code Quality Tests**: `tests/test_code_quality.py` (16 tests)
  - Module imports
  - Syntax validation
  - Dependency checks
  - Project structure integrity
  - Code standards compliance
  - Configuration file validation

#### 2. **GitHub Actions Workflows**
- **Main CI Pipeline** (`.github/workflows/ci.yml`)
  - Test matrix: Python 3.11-3.12 × Ubuntu/macOS
  - Automated testing on push/PR
  - Code coverage reporting (Codecov)
  - Security scanning (Trivy, Bandit)
  - Build distribution packages
  - Automatic releases

- **Lint & Format Workflow** (`.github/workflows/lint.yml`)
  - Code style checking (Ruff)
  - Format validation (Black)
  - Type checking (MyPy)
  - Import sorting (isort)

#### 3. **Pre-commit Hooks** (`.pre-commit-config.yaml`)
- Automatic code formatting
- Lint checking
- Type validation
- Security checks
- Docstring coverage
- File format validation

#### 4. **Test Infrastructure**
- **Enhanced conftest.py** - Fixtures and utilities
- **pytest.ini** - Test configuration
- **Quick check script** - Fast local validation
- **Full test runner** - Comprehensive test execution

#### 5. **Documentation**
- **CONTRIBUTING.md** - How to contribute
- **CI_CD_DOCUMENTATION.md** - Detailed CI/CD guide
- **TEST_CI_STATUS.md** - Test status and summary
- **This file** - Setup guide

---

## 🚀 Quick Start

### Option 1: Quick Check (30 seconds)
```bash
chmod +x quick-check.sh
./quick-check.sh
```
✅ Checks: Python version, tests discovery, formatting, linting, types

### Option 2: Full Test Suite
```bash
chmod +x run-tests.sh
./run-tests.sh
```

**Options**:
```bash
./run-tests.sh --coverage      # With coverage report
./run-tests.sh -m unit         # Only unit tests
./run-tests.sh --parallel      # Run in parallel
./run-tests.sh -v              # Verbose output
```

### Option 3: Manual Test Commands
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=pam_manager --cov-report=html

# Run specific tests
pytest -m unit
pytest -m integration
pytest tests/test_pam_manager_comprehensive.py -v

# Code quality checks
black --check .
ruff check .
mypy pam_manager --ignore-missing-imports
```

---

## 📊 Test Overview

### Test Categories
| Category | Tests | Purpose |
|----------|-------|---------|
| Unit | 40+ | Core functionality testing |
| Integration | Multiple | End-to-end workflows |
| Code Quality | 16 | Standards and structure |
| Platform | Included | OS-specific tests |
| Performance | 2+ | Large dataset handling |

### Coverage Requirements
- Minimum: 70%
- Target: 80%+
- Critical code: 90%+

### Test Locations
```
tests/
├── conftest.py                          # Fixtures and configuration
├── test_pam_manager_comprehensive.py    # 33 new comprehensive tests
├── test_code_quality.py                 # 16 new code quality tests
└── test_*.py                            # 200+ existing tests
```

---

## 🔧 Pre-commit Setup (Optional but Recommended)

### Installation
```bash
pip install pre-commit
pre-commit install
```

### What It Does
Automatically checks before each commit:
- Code formatting (Black)
- Import sorting (isort)
- Linting (Ruff)
- Type checking (MyPy)
- Security issues (Bandit)
- File formats (YAML, JSON, TOML)

### Manual Execution
```bash
# Run all checks
pre-commit run --all-files

# Auto-fix issues
black .
isort .
ruff check . --fix
```

---

## 🔄 GitHub Actions Workflows

### When They Run

**Main CI Pipeline** (`ci.yml`):
- ✅ On every push to main/develop
- ✅ On pull requests
- ✅ Daily schedule (2 AM UTC)
- ✅ On version tags (v*.*.*)

**Lint Workflow** (`lint.yml`):
- ✅ On every push to main/develop
- ✅ On pull requests

### What They Check

#### Tests Job
- Python 3.11, 3.12
- Ubuntu 20.04, latest, macOS latest
- Full test suite with coverage
- Codecov integration

#### Code Quality Job
- Code quality tests
- Security scanning (Bandit)
- SBOM generation

#### Build Job
- Create distributions
- Validate packages

#### Security Job
- Trivy vulnerability scan
- GitHub security tab upload

#### Documentation Job
- Check documentation exists
- Markdown validation

---

## 📈 Monitoring Test Results

### Locally
```bash
# Run tests with coverage report
pytest --cov=pam_manager --cov-report=html

# View in browser
open htmlcov/index.html
```

### On GitHub
1. Go to **Actions** tab
2. Click on workflow run
3. See test results and artifacts
4. View coverage badge (if configured)

### CI/CD Badges (for README)
```markdown
[![Tests](https://github.com/username/PAM-config/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/username/PAM-config/actions)
[![Lint](https://github.com/username/PAM-config/workflows/Lint%20%26%20Format%20Checks/badge.svg)](https://github.com/username/PAM-config/actions)
```

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install -e ".[dev]"
python -m pytest --collect-only
```

### "Tests pass locally but fail in CI"
```bash
# Check Python version (must be 3.11+)
python --version

# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall

# Clear caches
pytest --cache-clear
```

### "Pre-commit hooks fail"
```bash
# Auto-fix issues
black .
isort .
ruff check . --fix

# Then commit again
```

### "Coverage too low"
```bash
# Check coverage details
pytest --cov=pam_manager --cov-report=term-missing

# View HTML report
pytest --cov=pam_manager --cov-report=html
open htmlcov/index.html
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute code |
| [CI_CD_DOCUMENTATION.md](CI_CD_DOCUMENTATION.md) | Detailed CI/CD documentation |
| [TEST_CI_STATUS.md](TEST_CI_STATUS.md) | Test status and summary |
| [README.md](README.md) | Project overview |

---

## 🎯 Next Steps

### For Development
1. ✅ Install dev dependencies: `pip install -e ".[dev]"`
2. ✅ Run quick check: `./quick-check.sh`
3. ✅ Setup pre-commit: `pre-commit install`
4. ✅ Read [CONTRIBUTING.md](CONTRIBUTING.md)

### For First PR
1. ✅ Create feature branch: `git checkout -b feature/my-feature`
2. ✅ Write code and tests
3. ✅ Run local checks: `./run-tests.sh --coverage`
4. ✅ Fix any issues
5. ✅ Push and create PR
6. ✅ Wait for CI checks to pass

### For Release
1. ✅ Update version in `pyproject.toml`
2. ✅ Create tag: `git tag v0.3.0`
3. ✅ Push tag: `git push origin v0.3.0`
4. ✅ GitHub Actions handles the rest

---

## 🔑 Key Commands Reference

```bash
# Quick local check
./quick-check.sh

# Run all tests
./run-tests.sh --coverage

# Code quality
black .                                      # Format
ruff check . --fix                          # Lint
isort .                                     # Sort imports
mypy pam_manager --ignore-missing-imports   # Type check

# Pre-commit
pre-commit install                          # Setup
pre-commit run --all-files                  # Run all

# Pytest
pytest                                      # All tests
pytest -m unit                              # Unit only
pytest --cov=pam_manager                    # With coverage
pytest -v tests/test_specific.py            # Specific file
```

---

## 📊 Project Statistics

- **Total Tests**: 49 new tests (200+ with existing)
- **Test Categories**: Unit, Integration, Platform, Performance, Quality
- **CI Workflows**: 2 (CI pipeline + Linting)
- **Code Quality Tools**: 6 (Black, Ruff, MyPy, isort, Bandit, Interrogate)
- **Python Versions**: 3.11, 3.12
- **OS Support**: Linux, macOS (FreeBSD compatible)
- **Coverage Target**: 80%+

---

## ✅ Verification Checklist

- ✅ Tests can be discovered: `pytest --collect-only`
- ✅ YAML workflows are valid
- ✅ Pre-commit config is valid
- ✅ All scripts are executable
- ✅ Documentation is complete
- ✅ CI/CD ready to use

---

## 🆘 Support & Questions

**For issues or questions:**
1. Check [CI_CD_DOCUMENTATION.md](CI_CD_DOCUMENTATION.md)
2. See [CONTRIBUTING.md](CONTRIBUTING.md)
3. Review [TEST_CI_STATUS.md](TEST_CI_STATUS.md)
4. Open an issue on GitHub

---

## 📝 License

See [LICENSE](LICENSE) file.

**Last Updated**: 2026-08-19
