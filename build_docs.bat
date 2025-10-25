@echo off
REM Script rapide pour builder la documentation Sphinx

echo ========================================
echo Building Sphinx Documentation
echo ========================================

cd docs

REM Installer Sphinx si nécessaire
pip install sphinx sphinx-rtd-theme --quiet

REM Build HTML
sphinx-build -b html . _build/html

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Documentation built successfully!
    echo ========================================
    echo.
    echo Open: docs\_build\html\index.html
    echo.
    start _build\html\index.html
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
)

cd ..

