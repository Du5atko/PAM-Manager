# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for automated testing, code quality checks, security scanning, and release management.

## Workflows

### 1. Main CI Pipeline (`ci.yml`)

**Trigger:** Push to main/develop, PRs, daily schedule

**Jobs:**

#### Tests
- Runs on: Ubuntu 20.04/latest, macOS latest
- Python versions: 3.11, 3.12
- Steps:
  - Install system dependencies
  - Run pytest with coverage
  - Upload coverage to Codecov
  - Archive coverage reports

#### Integration Tests
- Runs platform-specific integration tests
- Requires main test suite to pass

#### Code Quality
- Runs code quality test suite
- Security checks with Bandit
- SBOM generation

#### Build
- Creates wheel and sdist distributions
- Validates distribution with twine
- Uploads build artifacts

#### Security Scan
- Trivy filesystem scan
- Uploads results to GitHub Security tab

#### Documentation
- Validates markdown
- Checks documentation exists

#### Publish Test
- Publishes to TestPyPI on version tags
- Allows pre-release testing

### 2. Lint & Format Workflow (`lint.yml`)

**Trigger:** Push to main/develop, PRs

**Jobs:**
- **Ruff Lint**: Checks code style and common errors
- **Black Format**: Validates code formatting
- **MyPy Type Check**: Type annotation validation
- **Import Sorting**: Checks import organization

## Running Tests Locally

### Quick Start
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=pam_manager --cov-report=html
```

### By Category
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Platform-specific tests
pytest -m platform

# Skip slow tests
pytest -m "not slow"

# Only security tests
pytest -m security
```

### Code Quality Checks
```bash
# Format check
black --check .

# Lint
ruff check .

# Type check
mypy pam_manager --ignore-missing-imports

# Security scan
bandit -r pam_manager

# All checks
pre-commit run --all-files
```

## Pre-commit Hooks

Install local pre-commit hooks to catch issues before committing:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # Run all checks
```

Hooks include:
- Trailing whitespace removal
- File format checking (YAML, JSON, TOML)
- Large file detection
- Black formatting
- isort import sorting
- Ruff linting
- MyPy type checking
- Bandit security checks

## Coverage Requirements

- **Minimum**: 70% code coverage
- **Target**: 80%+ code coverage
- **Critical code**: 90%+ coverage

View detailed coverage:
```bash
pytest --cov=pam_manager --cov-report=html
open htmlcov/index.html
```

## Testing on Different Python Versions

Local testing:
```bash
# Using pyenv (recommended)
pyenv local 3.11.0 3.12.0
pytest  # Tests both versions

# Using tox
pip install tox
tox
```

## Release Process

### Automatic Release
1. Update version in `pyproject.toml`:
   ```toml
   [project]
   version = "0.3.0"
   ```

2. Commit and tag:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 0.3.0"
   git tag v0.3.0
   git push origin main --tags
   ```

3. GitHub Actions automatically:
   - Runs full test suite
   - Builds distributions
   - Creates GitHub release
   - Publishes to PyPI (if configured)

### Manual Release
1. Go to GitHub releases
2. Create new release
3. Select tag
4. Add release notes
5. Publish

## Configuration Files

### `.github/workflows/ci.yml`
Main CI/CD pipeline configuration. Defines:
- Test matrix (Python versions, OS)
- Test commands and coverage requirements
- Build and publish steps
- Artifact retention

### `.github/workflows/lint.yml`
Code quality workflow. Defines:
- Linting standards
- Format validation
- Type checking rules

### `.pre-commit-config.yaml`
Local pre-commit hooks configuration. Includes:
- File format checks
- Code formatting (Black)
- Import sorting (isort)
- Linting (Ruff)
- Type checking (MyPy)
- Security checks (Bandit)

### `pyproject.toml`
Project metadata and tool configuration:
```toml
[project]
name = "pam-manager"
version = "0.2.0"

[project.optional-dependencies]
dev = [...]

[tool.pytest.ini_options]
testpaths = "tests"

[tool.black]
line-length = 88

[tool.isort]
profile = "black"

[tool.mypy]
python_version = "3.11"
```

### `pytest.ini`
Pytest configuration:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --tb=short -v
markers = 
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

## Environment Variables

Available in GitHub Actions:
- `GITHUB_TOKEN` - Git operations
- `CODECOV_TOKEN` - Coverage uploads (if set)
- `TEST_PYPI_API_TOKEN` - TestPyPI publishing (if set)

## Debugging Failed Tests

### Check Workflow Logs
1. Go to repository → Actions
2. Click on failed workflow run
3. Click on failed job
4. View detailed logs

### Common Failures

**Test Failures:**
- Check Python version compatibility
- Verify all dependencies installed
- Check for platform-specific issues

**Coverage Failures:**
- Run `pytest --cov=pam_manager` locally
- Compare local vs CI coverage
- Add missing tests

**Lint Failures:**
- Run `black .`, `ruff check .`
- Fix issues and commit
- Re-run workflow

**Security Warnings:**
- Review Bandit report
- Fix issues or add explanations
- Check Trivy results

## Performance Optimization

### Faster Test Runs
```bash
# Run tests in parallel
pip install pytest-xdist
pytest -n auto

# Run only changed tests
pytest --lf  # Last failed
pytest --ff  # Failed first
```

### Cache Management
```bash
# Clear pytest cache
pytest --cache-clear

# Clear pip cache
pip cache purge
```

## Monitoring & Alerts

- **GitHub**: Status checks on PRs
- **Codecov**: Coverage reports
- **Email**: Failed workflow notifications
- **Slack**: Optional integration

## Best Practices

1. **Run pre-commit before pushing**
   ```bash
   pre-commit run --all-files
   ```

2. **Test locally before PR**
   ```bash
   pytest --cov=pam_manager
   black --check .
   ruff check .
   mypy pam_manager --ignore-missing-imports
   ```

3. **Keep commits focused**
   - One feature per PR
   - Clean commit history
   - Clear commit messages

4. **Update tests with code**
   - Add tests for new features
   - Update tests for changes
   - Maintain coverage threshold

5. **Monitor CI status**
   - Fix failures promptly
   - Address review comments
   - Keep PRs up to date

## Troubleshooting

### "Tests pass locally but fail in CI"
- Check Python version: `python --version`
- Check OS compatibility
- Verify dependencies: `pip install -e ".[dev]"`
- Check for hardcoded paths or platform-specific code

### "Coverage is lower in CI"
- Ensure all platforms tested locally
- Run full test suite: `pytest --cov=pam_manager`
- Check for platform-specific code paths

### "Pre-commit hooks fail"
- Update tools: `pre-commit autoupdate`
- Fix issues: `black .`, `ruff check . --fix`
- Reinstall hooks: `pre-commit install`

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Ruff Linter](https://docs.astral.sh/ruff/)

## Support

For CI/CD issues:
1. Check workflow logs
2. Review configuration files
3. Run commands locally
4. Open issue with workflow output
5. Contact maintainers

## See Also

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines
- [README.md](README.md) - Project overview
- [docs/](docs/) - Detailed documentation
