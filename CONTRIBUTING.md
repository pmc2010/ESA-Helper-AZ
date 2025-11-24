# Contributing to ESA-Helper-AZ

Thank you for your interest in contributing to ESA-Helper-AZ! This document provides guidelines for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## How to Contribute

### Reporting Bugs

**Before submitting a bug report:**
- Check the [existing issues](https://github.com/pmc2010/ESA-Helper-AZ/issues) to avoid duplicates
- Check if the issue is already fixed in the latest version

**When submitting a bug report, include:**
- Clear, descriptive title
- Steps to reproduce the bug
- Expected behavior vs. actual behavior
- Your environment (OS, Python version, etc.)
- Error messages and logs
- Screenshots if applicable

### Suggesting Features

**Before submitting a feature request:**
- Check if the feature already exists
- Check the [existing feature requests](https://github.com/pmc2010/ESA-Helper-AZ/issues?q=is%3Aissue+label%3Aenhancement)

**When submitting a feature request, include:**
- Clear, descriptive title
- Detailed description of the feature
- Use cases and benefits
- Any alternative implementations you've considered

### Submitting Pull Requests

#### Step 1: Fork and Set Up
```bash
# Fork the repository on GitHub
# Clone your fork
git clone git@github.com:YOUR-USERNAME/ESA-Helper-AZ.git
cd ESA-Helper-AZ

# Add upstream remote
git remote add upstream git@github.com:pmc2010/ESA-Helper-AZ.git
```

#### Step 2: Create a Feature Branch
```bash
# Update from upstream
git fetch upstream
git checkout -b fix/issue-description main

# Or for features:
git checkout -b feature/feature-description main
```

#### Step 3: Make Your Changes

**Code Standards:**
- Follow [PEP 8](https://pep8.org/) for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep lines under 100 characters

**Testing:**
- Write tests for new functionality
- Ensure all tests pass locally: `pytest tests/`
- Maintain or improve code coverage

**Commits:**
- Write clear, descriptive commit messages
- Reference issues in commit messages: `Fix #123` or `Closes #456`
- Keep commits atomic (one logical change per commit)

#### Step 4: Run Tests and Checks
```bash
# Install dependencies
uv sync

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Check Python syntax
python3 -m py_compile app/*.py
```

#### Step 5: Push and Create PR
```bash
# Push your branch
git push origin feature/feature-description

# Create a pull request on GitHub
# Fill out the PR template completely
```

#### Step 6: Code Review
- Respond to reviewer feedback promptly
- Make requested changes in new commits
- Mark conversations as resolved after addressing them
- Re-request review when ready

## Development Setup

### Requirements
- Python 3.11+
- uv (Python package manager)
- Chrome/Chromium browser (for Selenium automation)
- LibreOffice (optional, for PDF generation)

### Quick Start
```bash
# Clone repository
git clone git@github.com:pmc2010/ESA-Helper-AZ.git
cd ESA-Helper-AZ

# Install dependencies
uv sync

# Run the application
uv run main.py
```

### Running Tests
```bash
# All tests
./scripts/run_all_tests.sh

# Specific test file
pytest tests/test_routes.py -v

# With coverage report
./scripts/test_coverage.sh
```

## Project Structure

```
ESA-Helper-AZ/
├── app/                           # Main application code
│   ├── automation.py             # Workflow orchestration
│   ├── classwallet.py            # Selenium browser automation
│   ├── invoice_generator.py      # Invoice generation
│   ├── routes.py                 # Flask API endpoints
│   ├── utils.py                  # Utility functions
│   ├── templates/                # HTML templates
│   └── static/                   # CSS, JavaScript
├── tests/                         # Test files
│   ├── conftest.py              # Test configuration
│   ├── test_routes.py           # API endpoint tests
│   ├── test_templates.py        # Template tests
│   └── test_*.py                # Other tests
├── data/                          # Data directory (user data)
│   ├── students.sample.json     # Sample student data
│   └── vendors.sample.json      # Sample vendor data
├── main.py                        # Application entry point
├── pyproject.toml                # Project configuration
└── README.md                      # Project overview
```

## Important Notes

### Security
- **Never commit credentials** - Use environment variables
- **Sensitive data files** - These are git-ignored:
  - `config.json` (credentials)
  - `data/students.json` (user data)
  - `data/vendors.json` (user data)
  - `data/esa_templates/` (user templates)

- **Report security issues** - Send security vulnerabilities to the maintainer privately instead of using GitHub issues

### Code Review Policy
- At least 1 approval required before merging
- All tests must pass
- Code must follow project standards
- Branch must be up to date with main

### Branch Naming Convention
- Features: `feature/brief-description`
- Bug fixes: `fix/brief-description`
- Documentation: `docs/brief-description`
- Chores: `chore/brief-description`

## Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Update CHANGELOG.md if applicable
- Add comments for complex logic

## Questions?

- Check existing documentation in the repo
- Review the [CLAUDE.md](CLAUDE.md) file for architecture details
- Open a GitHub discussion or issue for questions

Thank you for contributing to ESA-Helper-AZ!
