# Contributing to NeuralGraph Newsletter

Thank you for your interest in contributing to the NeuralGraph Newsletter project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up your development environment (see README.md)
4. Create a feature branch from `main`

## Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/neuralgraph-newsletter.git
cd neuralgraph-newsletter

# Set up the API
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints for function parameters and return values
- Write docstrings for public functions and classes
- Keep functions focused and small

## Making Changes

1. Create a branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes with clear, descriptive commits

3. Write or update tests as needed

4. Ensure all tests pass:
   ```bash
   pytest
   ```

5. Push to your fork and open a pull request

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Ensure CI checks pass
- Keep PRs focused on a single feature or fix

## Reporting Issues

When reporting issues, please include:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

## Questions?

Open an issue for questions or reach out to the maintainers.
