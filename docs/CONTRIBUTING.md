# Contributing to ArcGIS Client

Thank you for your interest in contributing to the ArcGIS Client project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment. By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Make (optional, for using Makefile commands)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/arcgis-client.git
   cd arcgis-client
   ```

## Development Setup

### 1. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Development Dependencies

```bash
make install-dev
# Or manually:
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 3. Set Up Pre-commit Hooks

```bash
pre-commit install
```

### 4. Configure Environment

```bash
make setup-env
# Edit .env with your configuration
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# Or for bug fixes:
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write code following our [coding standards](#coding-standards)
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests and Checks

```bash
# Run all checks
make check-all

# Or run individually:
make format      # Format code
make lint        # Run linters
make test        # Run tests
make security    # Security checks
```

### 4. Commit Your Changes

We follow conventional commits:

```bash
git commit -m "feat: add new spatial query feature"
git commit -m "fix: resolve connection timeout issue"
git commit -m "docs: update API documentation"
git commit -m "test: add integration tests for session manager"
```

Commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Maximum line length: 100 characters
- Use type hints for function signatures
- Write docstrings for all public functions/classes (Google style)

### Code Formatting

We use automated formatters:

```bash
# Format code
black . --line-length=100
isort . --profile black
```

### Linting

```bash
# Run linters
flake8 .
pylint *.py
mypy . --ignore-missing-imports
```

### Example Code Style

```python
from typing import Dict, List, Optional


def process_features(
    features: List[Dict[str, Any]],
    min_area: float,
    strict: bool = True
) -> Dict[str, Any]:
    """
    Process features for compliance checking.

    Args:
        features: List of GeoJSON features to process.
        min_area: Minimum required area in square miles.
        strict: Whether to apply strict validation.

    Returns:
        Dictionary containing processing results.

    Raises:
        ValueError: If features list is empty.
    """
    if not features:
        raise ValueError("Features list cannot be empty")

    # Implementation here
    return {"processed": len(features)}
```

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test function names

```python
def test_arcgis_client_handles_timeout_gracefully():
    """Test that client properly handles timeout errors."""
    client = ArcGISClient("http://slow-service.com")
    with pytest.raises(ArcGISError):
        client.query(where="1=1")
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_arcgis_client.py -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests
make test-integration
```

### Test Coverage

- Maintain test coverage above 80%
- Test edge cases and error conditions
- Include integration tests for critical paths

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def query_features(
    where_clause: str,
    max_records: int = 1000
) -> Dict[str, Any]:
    """
    Query features from ArcGIS Feature Service.

    This method executes a query against the configured ArcGIS Feature
    Service with automatic pagination and retry logic.

    Args:
        where_clause: SQL WHERE clause (e.g., "STATE_NAME = 'Texas'").
        max_records: Maximum records per page. Defaults to 1000.

    Returns:
        Dictionary containing query results in ArcGIS JSON format.

    Raises:
        ArcGISValidationError: If where_clause is invalid.
        ArcGISError: If the request fails.

    Example:
        >>> client = ArcGISClient(service_url)
        >>> results = client.query_features("STATE = 'CA'")
        >>> print(len(results['features']))
        58
    """
```

### README Updates

- Update README.md when adding features
- Include code examples for new functionality
- Update version numbers appropriately

## Submitting Changes

### Pull Request Process

1. **Update Documentation**: Ensure all relevant documentation is updated
2. **Add Tests**: Include tests for new features or bug fixes
3. **Run Checks**: Ensure all tests and linters pass
4. **Update Changelog**: Add entry to CHANGELOG.md (if exists)
5. **Create PR**: Submit pull request with clear description

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Description of testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
```

### Review Process

- Pull requests require at least one approval
- Address review feedback promptly
- Keep discussions professional and constructive

## Security

### Reporting Vulnerabilities

**Do not** create public issues for security vulnerabilities.

Instead, email: security@example.com

### Security Best Practices

- Never commit secrets or API keys
- Use environment variables for sensitive data
- Run `make security` before submitting
- Follow OWASP guidelines

## Questions?

- Check existing issues and discussions
- Ask questions in pull requests
- Contact maintainers if needed

Thank you for contributing! 🎉
