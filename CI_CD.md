# Automation & CI/CD Setup

This project includes comprehensive automation and CI/CD pipelines using GitHub Actions.

## Local Testing

### Prerequisites

```bash
pip install -r requirements-test.txt
```

### Quick Start

**macOS/Linux:**
```bash
chmod +x run_tests.sh run_lint.sh format_code.sh run_all.sh
./run_tests.sh
```

**Windows:**
```bash
run_tests.bat
```

### Available Scripts

#### Run Tests
Tests the application and generates coverage report:

**macOS/Linux:**
```bash
./run_tests.sh
```

**Windows:**
```bash
run_tests.bat
```

**Manual:**
```bash
pytest tests/ --cov=app --cov=bot --cov-report=html
```

#### Check Code Quality
Runs linting and formatting checks:

**macOS/Linux:**
```bash
./run_lint.sh
```

**Windows:**
```bash
run_lint.bat
```

**Manual:**
```bash
isort --check-only app bot tests
black --check app bot tests
flake8 app bot tests
```

#### Format Code
Automatically formats your code:

**macOS/Linux:**
```bash
./format_code.sh
```

**Windows:**
```bash
format_code.bat
```

**Manual:**
```bash
black app bot tests
isort app bot tests
```

#### Run All Checks
Formats, lints, and tests your code:

**macOS/Linux:**
```bash
./run_all.sh
```

**Windows:**
```bash
run_all.bat (not yet created, use individual scripts)
```

## GitHub Actions Workflows

### Workflow Files

Located in `.github/workflows/`:

1. **`tests.yml`** - Main test suite
2. **`lint.yml`** - Code quality checks

### Tests Workflow (`tests.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- All pull requests

**Actions:**
- Runs pytest on Python 3.10, 3.11, 3.12
- Calculates code coverage
- Uploads coverage to Codecov
- Builds Docker images
- Generates HTML coverage reports

**View Results:**
1. Go to GitHub repository
2. Click "Actions" tab
3. Click on a workflow run
4. View detailed logs and artifacts

### Lint Workflow (`lint.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- All pull requests

**Checks:**
- isort - Import sorting
- black - Code formatting
- flake8 - Python linting
- pylint - Advanced linting

**Continue on Error:**
- Lint warnings don't block PRs (can be improved)
- Fix warnings before merging

## Setting Up GitHub Actions

### 1. Enable Actions (if not already enabled)

GitHub Actions are enabled by default on public repositories.

For private repos:
1. Go to Settings → Actions → General
2. Choose "Allow all actions and reusable workflows"

### 2. Configure Codecov (Optional)

For coverage tracking on codecov.io:

1. Go to https://codecov.io
2. Sign up with GitHub
3. Enable this repository
4. Coverage badges and reports will appear automatically

### 3. Add Status Badges to README

```markdown
## CI/CD Status

[![Tests](https://github.com/YOUR_USERNAME/poetry-recommender/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/YOUR_USERNAME/poetry-recommender/actions/workflows/tests.yml)
[![Lint](https://github.com/YOUR_USERNAME/poetry-recommender/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/YOUR_USERNAME/poetry-recommender/actions/workflows/lint.yml)
```

### 4. Configure Branch Protection

To require passing checks before merging:

1. Go to Settings → Branches
2. Add rule for `main` or `develop`
3. Check "Require status checks to pass before merging"
4. Select checks to require:
   - `test (3.10, 3.11, 3.12)`
   - `lint`
   - `docker`

## Workflow Configuration

### Modifying Test Matrix

Edit `.github/workflows/tests.yml` to change Python versions:

```yaml
strategy:
  matrix:
    python-version: ["3.10", "3.11", "3.12"]  # Add/remove versions
```

### Modifying Coverage Requirements

```yaml
- name: Run tests with pytest
  run: |
    pytest tests/ \
      --cov=app \
      --cov=bot \
      --cov-report=xml \
      --cov-report=html \
      -v
```

### Adding New Workflow Steps

Example: Run performance tests

```yaml
- name: Run performance tests
  run: |
    pytest tests/performance/ --durations=10
```

## Pre-commit Hooks (Optional)

Automatically run checks before committing:

```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=127']

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        stages: [commit]
```

Then run checks automatically on every commit:

```bash
git add .
git commit -m "my changes"
# Hooks run automatically!
```

## Troubleshooting

### Tests Pass Locally but Fail in CI

- Check Python version differences (e.g., 3.10 vs 3.11)
- Verify all dependencies: `pip list | grep -E "pytest|sqlmodel|fastapi"`
- Check for environment-specific issues (paths, imports)

### Workflow Not Running

1. Check if Actions are enabled in Settings
2. Verify workflow file is in `.github/workflows/` directory
3. Check branch name matches trigger conditions
4. Look at Actions tab for error logs

### Coverage Not Uploading

1. Verify Codecov integration in settings
2. Check if `coverage.xml` is generated
3. Verify branch/token configuration

### Docker Build Fails

- Check `Dockerfile` and `bot.Dockerfile` syntax
- Verify all dependencies in `requirements.txt`
- Check for secrets or private files in build context

## Best Practices

1. **Commit before pushing** - Verify `./run_all.sh` passes
2. **Keep CI fast** - Use caching, parallelize when possible
3. **Test on push** - Find issues early, not on CI
4. **Descriptive commits** - Makes debugging easier
5. **Review PR checks** - Don't ignore failed tests
6. **Update dependencies** - Use Dependabot for automated updates

## Monitoring

### GitHub Actions Dashboard

1. Go to Actions tab
2. View workflow status
3. Click on a run for details
4. Check artifact downloads

### Email Notifications

Enable in GitHub Settings → Notifications:
- ✅ Workflow failures
- ✅ Successful workflows (optional)

### Integration with Slack

1. Create GitHub App in Slack workspace
2. Add `/github subscribe owner/repo workflows`
3. Receive workflow notifications in Slack

## Next Steps

1. ✅ Test locally: `./run_tests.sh`
2. ✅ Format code: `./format_code.sh`
3. ✅ Push to GitHub
4. ✅ Watch Actions tab
5. ✅ Monitor coverage reports
6. ✅ Set up branch protection
