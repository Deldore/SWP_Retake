@echo off
REM Script to run linting and formatting checks (Windows version)

echo.
echo 🔍 Running Linting & Formatting Checks...
echo =========================================

REM Check if linting tools are installed
python -c "import black" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing linting tools...
    pip install black flake8 isort pylint
)

echo.
echo 1️⃣  Checking imports with isort...
isort --check-only --diff app bot tests
if errorlevel 1 echo ⚠️  isort found issues

echo.
echo 2️⃣  Checking format with black...
black --check app bot tests
if errorlevel 1 echo ⚠️  black found issues

echo.
echo 3️⃣  Linting with flake8...
flake8 app bot tests --max-line-length=127 --statistics
if errorlevel 1 echo ⚠️  flake8 found issues

echo.
echo =========================================
echo ✅ Linting check complete!
echo.
echo To automatically fix issues, run:
echo   black app bot tests
echo   isort app bot tests
