# Contributing to MIMIC Explorer

Thank you for your interest in contributing! This document provides guidelines
for contributing to MIMIC Explorer.

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/khalidnawab/mimic-explorer.git
   cd mimic-explorer
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   ```

3. **Install in editable mode with dev dependencies**

   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

4. **Build the frontend** (requires Node.js 18+)

   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

## Running Tests

```bash
mimic-explorer --test
```

This runs the full test suite (62 tests) using an in-memory DuckDB instance —
no MIMIC-IV data files are needed.

## Code Style

- **Python**: Follow PEP 8. Use type hints where practical.
- **TypeScript/React**: Follow the existing patterns in `frontend/src/`.
- **Commits**: Write clear, concise commit messages describing what changed
  and why.

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Make your changes and ensure all tests pass (`mimic-explorer --test`).
3. If you add new functionality, add corresponding tests.
4. Submit a pull request with a clear description of the changes.

## Reporting Issues

- Use [GitHub Issues](https://github.com/khalidnawab/mimic-explorer/issues)
  to report bugs or request features.
- Include steps to reproduce, expected behavior, and actual behavior.
- Include your Python version and operating system.

## Scope

MIMIC Explorer is a research tool for the MIMIC-IV dataset. Contributions
should align with this scope: clinical data exploration, research workflows,
FHIR interoperability, and developer experience improvements.
