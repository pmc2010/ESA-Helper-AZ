# Test Suite Setup Summary

A comprehensive automated test suite has been created for ESA Helpers to verify changes and prevent regressions.

## What Was Created

### Python Tests (pytest)
- **`tests/conftest.py`**: Pytest configuration with fixtures for:
  - Flask app and test client
  - Sample data (students, vendors, categories)
  - Both Reimbursement and Direct Pay category configurations

- **`tests/test_routes.py`**: Flask route tests covering:
  - Main page loading and redirects
  - Setup and management pages
  - Expense category configuration
  - API endpoints

- **`tests/test_file_requirements.py`**: File requirement tests (CRITICAL) covering:
  - Reimbursement file requirements per category
  - Direct Pay file requirements per category
  - Differences between submission types
  - Configuration consistency and validation

### JavaScript Tests (Jest)
- **`tests/app.test.js`**: Form validation tests covering:
  - Expense category configurations
  - Direct Pay category configurations
  - Form validation logic
  - File requirement switching
  - Request type change behavior
  - File label consistency

### Configuration Files
- **`package.json`**: NPM configuration with Jest and Babel
- **`jest.config.js`**: Jest configuration for JavaScript tests
- **`.babelrc`**: Babel configuration for ES6+ support
- **`pyproject.toml`**: Updated with pytest dependencies

### Helper Scripts
- **`scripts/run_all_tests.sh`**: Run all Python and JavaScript tests
- **`scripts/test_file_requirements.sh`**: Run only critical file requirement tests
- **`scripts/test_coverage.sh`**: Generate coverage reports

### Documentation
- **`TESTING.md`**: Comprehensive testing guide (500+ lines)
- **`CLAUDE.md`**: Updated with testing quick start
- **`TEST_SETUP_SUMMARY.md`**: This file

## Quick Start

### Install Test Dependencies

```bash
# Python test dependencies
uv sync

# JavaScript test dependencies
npm install
```

### Run Tests

```bash
# All tests
./scripts/run_all_tests.sh

# File requirement tests (most critical)
./scripts/test_file_requirements.sh

# Coverage reports
./scripts/test_coverage.sh

# Individual frameworks
pytest tests/              # Python
npm test                   # JavaScript
```

## Test Coverage

### Python Tests: 47+ test cases
- **Routes**: 9 tests for Flask pages and API endpoints
- **File Requirements**: 38+ tests for Reimbursement and Direct Pay configurations

Key test classes:
- `TestMainRoutes`: Page loading and redirects
- `TestExpenseCategories`: Category configuration
- `TestReimbursementFileRequirements`: Original requirements
- `TestDirectPayFileRequirements`: New Direct Pay requirements
- `TestFileRequirementsDifferences`: Comparison logic
- `TestCategoryConsistency`: Configuration validation

### JavaScript Tests: 72+ test cases
- **Category Configuration**: 36 tests for expense categories
- **Form Validation**: 18 tests for validation logic
- **File Labels**: 6 tests for label consistency
- **Request Type Changes**: 12 tests for switching behavior

## Most Critical Tests

These tests verify the recent Direct Pay changes work correctly:

1. **`TestDirectPayFileRequirements`** (5 tests)
   - Verifies Invoice required for all Direct Pay categories
   - Verifies Receipt NOT required for Direct Pay
   - Verifies Curriculum only required for Supplemental Materials

2. **`TestFileRequirementsDifferences`** (4 tests)
   - Receipt removed from most Direct Pay
   - Invoice added to all Direct Pay
   - Curriculum optional except Supplemental
   - Attestation never in Direct Pay

3. **JavaScript `Direct Pay Categories`** (5 tests)
   - Verifies Direct Pay configuration matches requirements
   - Tests each category requirement
   - Validates configuration consistency

**Run these first after any changes**:
```bash
./scripts/test_file_requirements.sh
```

## Test Organization

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Pytest fixtures and configuration
├── test_routes.py           # Flask route tests
├── test_file_requirements.py # Critical requirement tests
└── app.test.js              # JavaScript validation tests
```

## Testing Workflow

### Before Making Changes
```bash
./scripts/run_all_tests.sh  # Establish baseline
```

### After Making Changes
```bash
# Run specific test suite for your change
pytest tests/test_file_requirements.py  # If changed categories
npm test -- --testNamePattern="Direct Pay"  # If changed form logic

# Run all tests
./scripts/run_all_tests.sh

# Check coverage
./scripts/test_coverage.sh
```

### Before Committing
```bash
# Ensure all tests pass
./scripts/run_all_tests.sh

# Check that no new issues introduced
git status
git diff
```

## Example: Testing a Change

Scenario: You add a new expense category and need to update file requirements.

1. **Update the code** in `routes.py` and `app.js`
2. **Update tests** to reflect new requirements:
   ```python
   # In tests/test_file_requirements.py
   def test_new_category_requirements(self, direct_pay_categories):
       category = 'New Category'
       required = direct_pay_categories[category]['required_fields']
       assert 'Invoice' in required
   ```
3. **Run tests**:
   ```bash
   pytest tests/test_file_requirements.py -v
   npm test -- --testNamePattern="New Category"
   ```
4. **Verify all tests pass**:
   ```bash
   ./scripts/run_all_tests.sh
   ```
5. **Check coverage**:
   ```bash
   ./scripts/test_coverage.sh
   ```
6. **Commit** only if all tests pass

## Coverage Reports

### Python Coverage
Generated in `htmlcov/index.html` via:
```bash
pytest --cov=app --cov-report=html
```

Shows:
- Lines of code covered by tests
- Gaps in test coverage
- Overall coverage percentage

### JavaScript Coverage
Generated via:
```bash
npm run test:coverage
```

Shows:
- Statement coverage
- Branch coverage
- Function coverage
- Line coverage

## Dependencies

### Python (pyproject.toml)
```toml
[project.optional-dependencies]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-flask>=1.2.0",
]
```

Install: `uv sync`

### JavaScript (package.json)
```json
{
  "devDependencies": {
    "@babel/preset-env": "^7.22.0",
    "babel-jest": "^29.0.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0"
  }
}
```

Install: `npm install`

## Troubleshooting

### Tests Won't Run

```bash
# Reinstall Python dependencies
uv sync

# Reinstall JavaScript dependencies
npm install --force

# Check Python/Node versions
python --version   # Should be 3.11+
node --version     # Should be 14+
```

### Specific Test Failing

```bash
# Run with verbose output
pytest -vv tests/test_file_requirements.py

# Run with print output
pytest -s tests/test_file_requirements.py

# Run single test
pytest tests/test_file_requirements.py::TestDirectPayFileRequirements::test_direct_pay_computer_hardware_requires_invoice_only -vv
```

### Coverage Not Generating

```bash
# Reinstall pytest-cov
uv pip install pytest-cov --force-reinstall

# Try again
pytest --cov=app --cov-report=html
```

## Next Steps

1. **Install dependencies**:
   ```bash
   uv sync
   npm install
   ```

2. **Run tests to verify setup**:
   ```bash
   ./scripts/run_all_tests.sh
   ```

3. **Review TESTING.md** for detailed testing guide

4. **Make changes** to the code and run tests to verify

5. **Check coverage** to ensure tests cover your changes

## File Summary

| File | Purpose | Tests |
|------|---------|-------|
| `conftest.py` | Pytest fixtures | Configuration |
| `test_routes.py` | Flask routes | 9 tests |
| `test_file_requirements.py` | File requirements | 38+ tests |
| `app.test.js` | Form validation | 72+ tests |
| `TESTING.md` | Testing guide | Documentation |
| `scripts/run_all_tests.sh` | Test runner | Helper script |
| `scripts/test_file_requirements.sh` | Critical tests | Helper script |
| `scripts/test_coverage.sh` | Coverage | Helper script |

## Questions?

See `TESTING.md` for comprehensive guide including:
- Detailed test descriptions
- How to write new tests
- Troubleshooting guide
- Performance tips
- CI/CD setup examples

Run `./scripts/run_all_tests.sh` to verify everything works!
