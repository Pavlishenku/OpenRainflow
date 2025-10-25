# Installation and Testing Guide

## Installation in a Clean Virtual Environment

### Step 1: Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

Or with all features:

```bash
pip install -e ".[dev,parallel]"
```

### Step 3: Verify Installation

```bash
python -c "import openrainflow; print(openrainflow.__version__)"
```

## Build Sphinx Documentation

### Method 1: Automatic Script (Windows)

```bash
build_docs.bat
```

This will:
1. Install Sphinx if necessary
2. Build HTML documentation
3. Automatically open index.html

### Method 2: Manual Commands

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Build documentation
cd docs
sphinx-build -b html . _build/html

# Open documentation
# Windows:
start _build\html\index.html

# Linux:
xdg-open _build/html/index.html

# Mac:
open _build/html/index.html
```

### Method 3: Makefile (Linux/Mac)

```bash
cd docs
make html
open _build/html/index.html
```

### Method 4: make.bat (Windows)

```bash
cd docs
make.bat html
start _build\html\index.html
```

## Run Unit Tests

### Install pytest

```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
pytest
```

### Tests with Detailed Report

```bash
pytest -v
```

### Tests with Code Coverage

```bash
pytest --cov=openrainflow --cov-report=html
```

Open report: htmlcov/index.html

### Tests by Module

```bash
pytest tests/test_rainflow.py -v
pytest tests/test_eurocode.py -v
pytest tests/test_damage.py -v
```

## Run Examples

```bash
python examples/basic_usage.py
python examples/advanced_analysis.py
python examples/custom_fatigue_curve.py
```

## Complete Verification Script

```bash
# 1. Create venv
python -m venv test_venv

# 2. Activate (Windows)
test_venv\Scripts\activate

# 3. Install
pip install --upgrade pip
pip install -e ".[dev,parallel]"

# 4. Run tests
pytest -v

# 5. Build documentation
cd docs
sphinx-build -b html . _build/html
cd ..

# 6. Run example
python examples/basic_usage.py
```

## Troubleshooting

### Error: "No module named 'numba'"

```bash
pip install numba
```

### Error: "No module named 'sphinx'"

```bash
pip install sphinx sphinx-rtd-theme
```

### Error: "pytest: command not found"

```bash
pip install pytest
```

### Sphinx Build Error: "Theme not found"

```bash
pip install sphinx-rtd-theme
```

### Permission Issues (Linux/Mac)

```bash
pip install --user -e .
```

### Numba Compilation Issues

Make sure you have a C compiler:

Windows:
- Install Microsoft C++ Build Tools
- https://visualstudio.microsoft.com/visual-cpp-build-tools/

Linux:
```bash
sudo apt-get install build-essential
```

Mac:
```bash
xcode-select --install
```

## Documentation Structure

After build, documentation contains:

```
docs/_build/html/
├── index.html              # Homepage
├── installation.html       # Installation guide
├── quickstart.html         # Quick start
├── user_guide.html         # Complete user guide
├── examples.html           # Detailed examples
├── api/
│   ├── rainflow.html       # Rainflow API
│   ├── eurocode.html       # Eurocode API
│   ├── damage.html         # Damage API
│   ├── parallel.html       # Parallel API
│   └── utils.html          # Utils API
├── contributing.html       # Contributing guide
└── changelog.html          # Version history
```

## Validation Checklist

- [ ] Virtual environment created
- [ ] Dependencies installed (numpy, numba, scipy)
- [ ] Package installed (pip install -e .)
- [ ] Unit tests pass (pytest)
- [ ] Documentation built (cd docs && make html)
- [ ] Documentation accessible (open docs/_build/html/index.html)
- [ ] Basic example executed (python examples/basic_usage.py)
- [ ] Import works (import openrainflow)

## Expected Performance

On a modern system (i7, 16GB RAM):

- Numba compilation: ~1s (first run)
- Rainflow 1M points: ~0.05s (after compilation)
- Sphinx build: ~5-10s
- Unit tests: ~5-15s
- Basic example: ~2-3s

## Support

If you encounter problems:

1. Check Python version: python --version (>= 3.8)
2. Check pip: pip --version
3. Check dependencies: pip list | grep -E "numpy|numba|scipy"
4. Review complete error logs
5. Create a GitHub issue with:
   - Python version
   - Operating system
   - Complete error message
   - Result of pip list
