# Contributing to PAM Manager

Thank you for your interest in contributing to PAM Manager! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Assume good intentions
- Help others learn and grow

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- pip or poetry

### Development Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/PAM-config.git
cd PAM-config
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies:**
```bash
pip install -e ".[dev]"
```

4. **Install pre-commit hooks:**
```bash
pip install pre-commit
pre-commit install
```

### Running Tests Locally

**All tests:**
```bash
pytest
```

**Specific test categories:**
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# With coverage
pytest --cov=pam_manager --cov-report=html
```

**Specific test file:**
```bash
pytest tests/test_core.py -v
```

### Code Quality Checks

**Run all checks:**
```bash
# Format check
black --check .

# Linting
ruff check .

# Type checking
mypy pam_manager --ignore-missing-imports

# All via pre-commit
pre-commit run --all-files
```

**Auto-fix issues:**
```bash
# Format code
black .

# Sort imports
isort .

# Ruff auto-fixes
ruff check . --fix
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-feature` - New features
- `bugfix/fix-issue-description` - Bug fixes
- `docs/update-documentation` - Documentation updates
- `refactor/improve-code-structure` - Code refactoring
- `test/add-tests-for-feature` - Test additions

### Commit Messages

Follow conventional commits format:
```
type(scope): description

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or changes
- `chore`: Build, dependencies, etc.

**Example:**
```
feat(config): add YAML validation support

Implement validation for YAML configuration files with
detailed error reporting for invalid structures.

Closes #123
```

### Pull Request Process

1. **Fork and create a feature branch**
```bash
git checkout -b feature/your-feature
```

2. **Make your changes**
   - Write clear, self-documenting code
   - Add/update tests for your changes
   - Update documentation as needed

3. **Ensure all tests pass:**
```bash
pytest --cov=pam_manager
black --check .
ruff check .
mypy pam_manager --ignore-missing-imports
```

4. **Commit and push:**
```bash
git add .
git commit -m "feat(scope): description"
git push origin feature/your-feature
```

5. **Create a Pull Request**
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe what your changes do
   - Include any breaking changes

6. **Respond to feedback**
   - Address review comments
   - Push additional commits
   - Don't force-push unless requested

## Writing Tests

### Test Structure

```python
import pytest

@pytest.mark.unit
class TestFeatureName:
    """Test feature description."""
    
    def test_specific_behavior(self, temp_dir):
        """Test specific behavior with clear description."""
        # Arrange
        test_data = "setup"
        
        # Act
        result = function_under_test(test_data)
        
        # Assert
        assert result == "expected"
```

### Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.platform` - Platform-specific tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.security` - Security-related tests

### Fixtures

Use conftest.py fixtures:
```python
def test_with_fixtures(temp_config_file, mock_pam_modules):
    """Test using provided fixtures."""
    # Use fixtures in your test
    pass
```

### Coverage Requirements

- Aim for >80% code coverage
- Cover main paths and edge cases
- Include error condition tests

## Documentation

### Code Comments

```python
def complex_function(param: str) -> dict:
    """
    Brief description.
    
    Longer description if needed.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input provided
        
    Example:
        >>> result = complex_function("test")
        >>> result['key']
        'value'
    """
```

### Update Documentation

- Add docstrings to new functions/classes
- Update README.md for new features
- Update docs/ for significant changes
- Keep examples current

## Reporting Issues

### Bug Reports

Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- System info (OS, Python version, PAM version)
- Relevant logs or error messages

### Feature Requests

Include:
- Clear description of feature
- Why it would be useful
- Example usage
- Potential challenges

## Project Structure

```
PAM-config/
├── pam_manager/          # Main package
│   ├── core/            # Core functionality
│   ├── config/          # Configuration handling
│   ├── discovery/       # PAM module discovery
│   ├── policy/          # Policy validation
│   ├── platform/        # Platform detection
│   └── ...
├── tests/               # Test suite
│   ├── conftest.py     # Pytest configuration
│   ├── test_*.py       # Test modules
│   └── ...
├── docs/                # Documentation
├── .github/workflows/   # CI/CD workflows
├── pyproject.toml      # Project metadata
├── pytest.ini          # Pytest config
└── .pre-commit-config.yaml  # Pre-commit hooks
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`
5. GitHub Actions will create release automatically

## CI/CD Pipeline

Our automated pipeline runs:

- **Tests**: Python 3.11, 3.12 on Ubuntu, macOS
- **Code Quality**: Black, ruff, mypy
- **Coverage**: Tracked via Codecov
- **Security**: Trivy, Bandit scans
- **Build**: Wheel and sdist generation
- **Release**: Automatic on version tags

See `.github/workflows/` for workflow definitions.

## Common Issues

### Tests fail locally but pass in CI

1. Check Python version: `python --version`
2. Check dependencies: `pip list`
3. Clear cache: `pytest --cache-clear`
4. Recreate venv if needed

### Pre-commit hooks failing

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run all checks
pre-commit run --all-files

# Fix issues
black .
isort .
ruff check . --fix
```

### Import issues

```bash
# Reinstall in development mode
pip install -e ".[dev]"

# Check Python path
python -c "import sys; print(sys.path)"
```

## Getting Help

- **Questions**: Open a Discussion
- **Bugs**: Open an Issue
- **Security issues**: Email security@example.com (don't open public issues)
- **Chat**: Join our community discussions

## Recognition

Contributors will be recognized in:
- README.md
- Release notes
- GitHub contributors page

Thank you for contributing! 🎉
