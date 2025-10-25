# Contributing to OpenRainflow

Thank you for your interest in contributing to OpenRainflow.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/openrainflow/openrainflow.git
cd openrainflow
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev,parallel]"
```

## Code Style

- Follow PEP 8 style guide
- Use Black for code formatting: black openrainflow/
- Maximum line length: 100 characters
- Use type hints where appropriate

## Testing

Run tests before submitting:
```bash
pytest
pytest --cov=openrainflow  # With coverage
```

Add tests for new features in tests/ directory.

## Performance Considerations

- Use Numba JIT compilation for computational bottlenecks
- Profile code with: python -m cProfile -o profile.stats your_script.py
- Use NumPy vectorization where possible
- Cache expensive computations

## Documentation

- Update README.md for new features
- Add docstrings (Google style) to all functions
- Include examples for complex features
- Update CHANGELOG.md

## Pull Request Process

1. Create a feature branch: git checkout -b feature-name
2. Make your changes with clear commit messages
3. Add/update tests
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

## Code Review Checklist

- Tests added/updated
- Documentation updated
- Code formatted with Black
- No linter warnings
- Performance tested for computational functions
- Examples added if appropriate

## Bug Reports

Include:
- Python version
- OpenRainflow version
- Minimal reproducible example
- Expected vs actual behavior
- Error messages/stack traces

## Feature Requests

Describe:
- Use case
- Proposed API
- Expected behavior
- Any alternatives considered

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
