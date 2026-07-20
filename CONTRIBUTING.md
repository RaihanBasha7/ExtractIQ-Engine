# Contributing to ExtractIQ Engine

Thank you for considering contributing! We welcome contributions of all kinds.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Issues

- Check existing issues to avoid duplicates.
- Use a clear, descriptive title.
- Include steps to reproduce for bugs.
- Include environment details (Python version, OS, etc.).

### Submitting Pull Requests

1. Fork the repository.
2. Create a feature branch from `main`.
3. Set up your development environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   cd backend
   pip install -r requirements.txt -r requirements-dev.txt
   pre-commit install
   ```

4. Make your changes.
5. Run the test suite:

   ```bash
   cd backend
   python -m pytest
   ```

6. Ensure formatting is correct:

   ```bash
   black --check app/ tests/
   isort --check-only app/ tests/
   flake8 app/ tests/
   ```

7. Commit with a clear message.
8. Push and open a Pull Request.

### Development Guidelines

- Maintain backward compatibility.
- Do not modify extraction pipeline logic.
- Do not modify prompts.
- Keep API responses backward compatible.
- Add tests for new functionality.
- Update documentation as needed.

## Project Structure

```
backend/
    app/           # Application code
    tests/         # Test suite
    scripts/       # Utility scripts
    Dockerfile     # Docker build
```

## Testing

```bash
cd backend
python -m pytest          # Run tests
python -m pytest --cov    # With coverage
python -m pytest -v       # Verbose
```
