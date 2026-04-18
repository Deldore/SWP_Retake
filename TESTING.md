# Testing Guide

## Overview

This project includes a comprehensive test suite with unit tests, integration tests, and automated CI/CD pipelines using GitHub Actions.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_recommender.py      # Tests for recommendation service
├── test_reminder.py         # Tests for reminder service  
├── test_api.py             # API endpoint tests
└── __init__.py
```

## Setup

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Install All Dependencies

```bash
pip install -r requirements.txt -r requirements-test.txt
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=app --cov=bot --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`

### Run Specific Test File

```bash
pytest tests/test_recommender.py
```

### Run Specific Test Class

```bash
pytest tests/test_recommender.py::TestUpsertUser
```

### Run Specific Test

```bash
pytest tests/test_recommender.py::TestUpsertUser::test_create_new_user
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Tests in Parallel

```bash
pip install pytest-xdist
pytest -n auto
```

## Test Coverage

### Current Coverage

Run coverage report:

```bash
pytest --cov=app --cov=bot --cov-report=term-missing
```

### View HTML Coverage Report

```bash
pytest --cov=app --cov=bot --cov-report=html
open htmlcov/index.html
```

## GitHub Actions Workflows

### 1. Tests Workflow (`.github/workflows/tests.yml`)

Runs on every push to `main` and `develop` branches, plus all PRs.

**Features:**
- Tests on Python 3.10, 3.11, 3.12
- Code coverage reporting
- Docker build verification
- Codecov integration

**Runs:**
- Pytest with coverage
- Flake8 linting
- Docker image build

### 2. Lint Workflow (`.github/workflows/lint.yml`)

Runs on every push and PR.

**Features:**
- isort (import sorting)
- black (code formatting)
- flake8 (linting)
- pylint (additional linting)

## Writing Tests

### Test File Naming

- Test files must start with `test_` prefix
- Test classes must start with `Test` prefix
- Test methods must start with `test_` prefix

### Using Fixtures

Common fixtures from `conftest.py`:

```python
def test_something(session: Session, test_user: UserProfile, test_poem: Poem):
    """Test with database fixtures."""
    # session - in-memory database session
    # test_user - sample English-speaking user
    # test_poem - sample English poem
    # test_user_ru - sample Russian-speaking user
    # test_poem_ru - sample Russian poem
    pass
```

### Example Test

```python
import pytest
from sqlmodel import Session
from app.models.tables import UserProfile

class TestMyFeature:
    """Tests for my feature."""
    
    def test_something(self, session: Session):
        """Test that something works."""
        user = UserProfile(telegram_user_id=123)
        session.add(user)
        session.commit()
        
        assert user.id is not None
```

### Async Tests

```python
import pytest
from pytest import mark

@mark.asyncio
async def test_async_function():
    """Test async functions."""
    result = await some_async_function()
    assert result is not None
```

## Test Categories

### Unit Tests

Test individual functions in isolation:
- `test_recommender.py` - Recommendation logic
- `test_reminder.py` - Reminder service
- `test_api.py` - API endpoints

### Integration Tests

Test interactions between components:
- Database operations with real models
- API endpoints with database
- Service interactions

## Debugging Tests

### Run with Print Statements

```bash
pytest -s tests/test_recommender.py::TestUpsertUser::test_create_new_user
```

The `-s` flag captures and displays `print()` output.

### Run with PDB Debugger

```bash
pytest --pdb tests/test_recommender.py::TestUpsertUser::test_create_new_user
```

Drops into Python debugger on test failure.

### Run with Traceback

```bash
pytest --tb=long tests/test_recommender.py
```

### Show Local Variables on Failure

```bash
pytest -l tests/test_recommender.py
```

## Continuous Integration

### Before Pushing Code

1. **Run tests locally:**
   ```bash
   pytest
   ```

2. **Check code quality:**
   ```bash
   black app bot
   isort app bot
   flake8 app bot
   ```

3. **Fix issues:**
   ```bash
   black --fix app bot
   isort app bot
   ```

### GitHub Actions Status

Check workflow status in:
- Actions tab on GitHub
- PR comments and status checks
- Commit badges

### Build Badge

Add to README.md:

```markdown
[![Tests](https://github.com/YOUR_USERNAME/poetry-recommender/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR_USERNAME/poetry-recommender/actions/workflows/tests.yml)
[![Lint](https://github.com/YOUR_USERNAME/poetry-recommender/actions/workflows/lint.yml/badge.svg)](https://github.com/YOUR_USERNAME/poetry-recommender/actions/workflows/lint.yml)
```

## Troubleshooting

### Import Errors in Tests

Make sure you're running pytest from the project root:

```bash
cd /path/to/poetry-recommender
pytest
```

### Database Errors

Tests use in-memory SQLite, not the actual database. This is isolated and fast.

### Fixture Not Found

Ensure `conftest.py` is in the `tests/` directory.

### Tests Pass Locally but Fail in CI

- Check Python version differences
- Verify all dependencies in `requirements-test.txt`
- Check for timezone-dependent tests (use UTC in tests)

## Best Practices

1. **Keep tests focused** - One test per behavior
2. **Use descriptive names** - `test_create_user_with_invalid_id` is better than `test_create`
3. **Test both success and failure** - Happy path and edge cases
4. **Use fixtures** - Don't create test data repeatedly
5. **Isolate tests** - Each test should be independent
6. **Mock external services** - Don't call real APIs in tests
7. **Keep tests fast** - Slow tests get skipped

## Coverage Goals

Aim for:
- **>80%** overall coverage
- **>90%** for core services (recommender.py, reminder.py)
- **100%** for critical business logic

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [pytest-cov](https://github.com/pytest-dev/pytest-cov)
- [Coverage.py](https://coverage.readthedocs.io/)
