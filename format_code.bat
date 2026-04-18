@echo off
REM Script to format code automatically (Windows version)

echo.
echo 🎨 Formatting Code...
echo =====================

REM Check if formatting tools are installed
python -c "import black" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing formatting tools...
    pip install black isort
)

echo.
echo Formatting with black...
black app bot tests

echo.
echo Organizing imports with isort...
isort app bot tests

echo.
echo =====================
echo ✅ Code formatted!
