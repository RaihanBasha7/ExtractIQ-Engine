# Contributing

Thank you for considering contributing to ExtractIQ Engine! We welcome contributions of all kinds: bug fixes, features, documentation, and tests.

## Getting started

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/my-feature` or `fix/my-fix`.
3. Set up the development environment (see [README](README.md)).
4. Make your changes.
5. Run tests: `pytest` in the `backend/` directory.
6. Run linting: `black . && isort . && flake8`.
7. Push and open a pull request.

## Code style

- Python: Follow [PEP 8](https://peps.python.org/pep-0008/). Use `black` and `isort` for formatting.
- TypeScript: Follow the existing ESLint + Prettier configuration.
- Use descriptive variable names, avoid abbreviations.
- Do not add unnecessary comments — let the code speak.

## Testing

- All new features should include tests.
- Maintain or improve test coverage (target: 80%+).
- Run `pytest --cov=app` in `backend/` before submitting.

## Commit messages

Write clear, concise commit messages. Use the imperative mood:
- `Add batch upload retry logic`
- `Fix PDF parser encoding fallback`
- `Update dependencies`

## Pull requests

- Link to the related issue.
- Ensure all CI checks pass.
- Keep changes focused — one PR per feature/fix.

## Questions?

Open a [Discussion](https://github.com/anomalyco/ExtractIQ-Engine/discussions) or check the existing issues.
