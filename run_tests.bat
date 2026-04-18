@echo off
REM Script to run tests locally with coverage (Windows version)

echo.
echo 🧪 Running Poetry Bot Tests...
echo ================================

REM Check if test requirements are installed
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing test dependencies...
    pip install -r requirements-test.txt
)

REM Run pytest with coverage
echo.
echo Running pytest with coverage report...
pytest tests/ ^
    --cov=app ^
    --cov=bot ^
    --cov-report=html ^
    --cov-report=term-missing ^
    -v

REM Show coverage summary
echo.
echo ================================
echo ✅ Tests complete!
echo 📊 Coverage report generated in htmlcov/index.html
echo.
echo To view the report, run:
echo   start htmlcov/index.html
