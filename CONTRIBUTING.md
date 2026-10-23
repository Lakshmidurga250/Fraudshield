# Contributing to FraudShield

Thank you for your interest in contributing to FraudShield!

## Code of Conduct
Please maintain a respectful, inclusive, and professional environment.

## Development Workflow

1. Fork or clone the repository.
2. Create a clean feature branch:
   ```powershell
   git checkout -b feat/your-feature-name
   ```
3. Set up your local virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
4. Verify tests pass before modifying code:
   ```powershell
   python -m pytest
   ```
5. Implement your change with corresponding unit/integration tests.
6. Verify code style and linting:
   ```powershell
   python -m ruff check .
   python -m ruff format .
   ```
7. Commit changes with atomic, conventional commit messages:
   - `feat(scope): short description`
   - `fix(scope): fix description`
   - `test(scope): test description`
   - `docs(scope): documentation update`
