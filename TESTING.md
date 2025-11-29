# Testing Guide for ESA Helpers

This document describes how to run tests for the ESA Helpers application to verify that changes work correctly.

## Overview

The test suite includes:
- **Python Unit Tests**: Test Flask routes, API endpoints, and file requirement configurations
- **JavaScript Unit Tests**: Test form validation logic and category configurations
- **Integration Tests**: Test workflows combining multiple components

## Test Architecture

```
tests/
├── __init__.py                      # Python test package
├── conftest.py                      # Pytest configuration and fixtures
├── test_templates.py               # Template CRUD operations (19 tests)
├── test_direct_pay.py              # Direct Pay submission workflow (7 tests)
├── test_file_requirements.py       # File requirement validation (16 tests)
├── test_pdf_splitting.py           # PDF utilities and temp files (27 tests)
├── test_submission_logging.py      # Submission logging and history (10 tests)
├── test_routes.py                  # Flask routes and API endpoints (15 tests)
└── app.test.js                     # JavaScript form validation tests
```

## Test Statistics

- **Total Python Tests**: 89 (all passing ✓)
- **Code Coverage**: 21% overall
- **Last Updated**: November 2024

## Quick Start

### Install Test Dependencies

```bash
# Install Python test dependencies
uv sync

# Install JavaScript test dependencies
npm install
```

### Run All Tests

```bash
# Python tests
pytest

# JavaScript tests
npm test

# Run both (see scripts below)
./scripts/run_all_tests.sh
```

## Python Testing

### Running Python Tests

```bash
# Run all Python tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_routes.py

# Run specific test class
pytest tests/test_file_requirements.py::TestReimbursementFileRequirements

# Run specific test
pytest tests/test_file_requirements.py::TestReimbursementFileRequirements::test_computer_hardware_requires_receipt

# Run with coverage report
pytest --cov=app

# Run with coverage and generate HTML report
pytest --cov=app --cov-report=html
```

### Python Test Files

#### `tests/conftest.py`
Pytest configuration file that provides:
- Flask app fixture (`app`)
- Test client fixture (`client`)
- CLI test runner fixture (`runner`)
- Sample data fixtures (students, vendors, categories)

#### `tests/test_templates.py` (19 tests)
Tests for template CRUD operations and workflows:
- Saving new templates
- Updating existing templates
- Deleting templates
- Retrieving templates by ID and student
- File path validation
- Direct Pay vs Reimbursement templates
- Complete end-to-end template workflows

Key test classes:
- `TestTemplateSaving`: Template creation
- `TestTemplateLoading`: Template retrieval
- `TestTemplateDeletion`: Template deletion
- `TestTemplateUtilityFunctions`: Utility function tests
- `TestTemplateFileValidation`: File path validation
- `TestTemplateIntegration`: Complete workflows

#### `tests/test_direct_pay.py` (7 tests)
Tests for Direct Pay submission workflow:
- Basic Direct Pay submission flow
- Vendor search term configuration
- Login failure handling
- Vendor selection failures
- Submission logging
- Auto-submit vs manual review modes
- Additional info field population

Key test classes:
- `TestDirectPayWorkflow`: Core Direct Pay tests
- `TestDirectPayAdditionalInfo`: Info field tests

#### `tests/test_file_requirements.py` (16 tests)
Tests for file requirement configurations:
- Reimbursement file requirements for each category
- Direct Pay file requirements for each category
- Differences between Reimbursement and Direct Pay
- Configuration consistency

Key test classes:
- `TestReimbursementFileRequirements`: Original file requirements
- `TestDirectPayFileRequirements`: Direct Pay-specific requirements
- `TestFileRequirementsDifferences`: Comparison between types
- `TestCategoryConsistency`: Configuration validation

#### `tests/test_pdf_splitting.py` (27 tests)
Tests for PDF operations and temporary file management:
- PDF splitting (single and multi-page)
- Temp file directory creation
- Temp file retrieval and deletion
- Path traversal protection
- Cleanup of old and all temp files
- API endpoints for PDF operations
- Manage temp files page

Key test classes:
- `TestSplitPdfUtility`: PDF splitting utilities
- `TestTempFileManagement`: Temp file operations
- `TestPdfSplitApi`: API endpoints
- `TestTempFilesApi`: Temp files endpoints
- `TestManageTempFilesPage`: Web page tests

#### `tests/test_submission_logging.py` (10 tests)
Tests for submission logging and history:
- Log entry creation with all fields
- Category and comment field inclusion
- Master history file updates
- Optional field handling
- History sorting (newest first)
- Direct Pay vs Reimbursement logging
- Missing field handling

Key test classes:
- `TestSubmissionLogging`: All logging tests

#### `tests/test_routes.py` (15 tests)
Tests for Flask routes and API endpoints:
- Index page loading/redirects
- Setup, manage students, manage vendors pages
- Manage templates, manage logs, submission history pages
- Expense category configuration
- Template, vendor, PO number, credentials, and settings API endpoints

Key test classes:
- `TestMainRoutes`: Main page and route tests
- `TestExpenseCategories`: Category configuration tests
- `TestAPIEndpoints`: API endpoint tests

### Running Python Tests Examples

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run all template tests
uv run python -m pytest tests/test_templates.py -v

# Run all file requirement tests
uv run python -m pytest tests/test_file_requirements.py -v

# Run only Direct Pay requirement tests
uv run python -m pytest tests/test_file_requirements.py::TestDirectPayFileRequirements -v

# Run direct pay submission tests
uv run python -m pytest tests/test_direct_pay.py -v

# Run PDF operations tests
uv run python -m pytest tests/test_pdf_splitting.py -v

# Run submission logging tests
uv run python -m pytest tests/test_submission_logging.py -v

# Run routes and API tests
uv run python -m pytest tests/test_routes.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=app --cov-report=html

# Run and stop on first failure
uv run python -m pytest tests/ -x

# Run with print statements visible
uv run python -m pytest tests/ -s
```

## JavaScript Testing

### Running JavaScript Tests

```bash
# Run all JavaScript tests
npm test

# Run with watch mode (re-run on file changes)
npm run test:watch

# Run with coverage report
npm run test:coverage

# Run specific test file
npm test -- app.test.js
```

### JavaScript Test Files

#### `tests/app.test.js`
Tests for JavaScript form validation and category configuration:
- Expense category configurations
- Direct Pay category configurations
- Category configuration consistency
- File requirement differences
- Form validation logic
- File labels

Key test suites:
- `Expense Categories Configuration`: Category definitions
- `Form Validation Logic`: Form validation functions
- `File Labels Configuration`: File label consistency

### Running JavaScript Tests Examples

```bash
# Run JavaScript tests
npm test

# Run with watch mode for development
npm run test:watch

# Run with coverage
npm run test:coverage

# Show test output with coverage details
npm test -- --coverage --verbose
```

## Continuous Integration

### GitHub Actions (Optional Setup)

You can add a `.github/workflows/tests.yml` file to run tests automatically on pull requests:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run Python tests
        run: pytest --cov=app
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"
      - name: Install JavaScript dependencies
        run: npm ci
      - name: Run JavaScript tests
        run: npm test
```

## Test Coverage

### Python Coverage

Generate coverage report:
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

This creates an HTML report in `htmlcov/index.html` showing:
- Lines covered by tests
- Lines missing coverage
- Overall coverage percentage

### JavaScript Coverage

Generate coverage report:
```bash
npm run test:coverage
```

This shows coverage for:
- Statements
- Branches
- Functions
- Lines

## Key Test Scenarios

### File Requirement Tests (Most Important)

These tests verify the recent Direct Pay changes work correctly:

1. **Reimbursement Requirements**
   - Computer Hardware: Receipt only
   - Curriculum: Receipt only
   - Tutoring Facility: Receipt + Invoice
   - Tutoring Individual: Receipt + Invoice + Attestation
   - Supplemental Materials: Curriculum + Receipt

2. **Direct Pay Requirements**
   - Computer Hardware: Invoice only
   - Curriculum: Invoice only
   - Tutoring Facility: Invoice only
   - Tutoring Individual: Invoice only
   - Supplemental Materials: Invoice + Curriculum

3. **Key Differences**
   - Receipt is removed from Direct Pay (except Supplemental)
   - Invoice is required for all Direct Pay
   - Curriculum is optional in Direct Pay (except Supplemental)
   - Attestation is never required in Direct Pay

### Form Validation Tests

These test ensure the form properly validates based on request type:

1. **Request Type Switching**
   - Switching from Reimbursement to Direct Pay updates requirements
   - File selections are cleared when switching types
   - UI updates to show new required files

2. **File Validation**
   - Form requires all necessary files
   - Form enables submit button only when all files present
   - Form disables submit if required file is removed

## Writing New Tests

### Adding Python Tests

1. Create test in appropriate file or new test file
2. Use descriptive test names starting with `test_`
3. Use fixtures from `conftest.py`
4. Use assertions to verify behavior

Example:
```python
def test_my_feature(client, sample_students):
    """Test my new feature"""
    response = client.get('/my-route')
    assert response.status_code == 200
    assert b'expected_content' in response.data
```

### Adding JavaScript Tests

1. Add test case to appropriate `describe` block
2. Use descriptive test names
3. Test both positive and negative cases
4. Keep tests focused and isolated

Example:
```javascript
test('should validate required files', () => {
  const required = ['Invoice'];
  const selected = { 'Invoice': 'file.pdf' };

  const isValid = required.every(ft => selected[ft]);
  expect(isValid).toBe(true);
});
```

## Troubleshooting

### Python Tests Failing

```bash
# Check Python version
python --version  # Should be 3.11+

# Re-install dependencies
uv sync

# Run with verbose output to see errors
pytest -vv

# Run specific failing test with output
pytest -s tests/test_file_requirements.py::TestFileRequirementsDifferences::test_receipt_removed_in_direct_pay
```

### JavaScript Tests Failing

```bash
# Clear Jest cache
npm test -- --clearCache

# Check Node version
node --version  # Should be 14+

# Re-install dependencies
npm install

# Run with verbose output
npm test -- --verbose
```

### Missing Dependencies

```bash
# Python
uv sync

# JavaScript
npm install

# Both
./scripts/install_all_deps.sh
```

## Test Results Interpretation

### Python Test Output
```
tests/test_file_requirements.py::TestReimbursementFileRequirements::test_computer_hardware_requires_receipt PASSED
tests/test_routes.py::TestMainRoutes::test_index_redirects_without_config PASSED

======================== 47 passed in 0.15s ========================
```

✓ All tests passed

### JavaScript Test Output
```
PASS  tests/app.test.js
  Expense Categories Configuration
    ✓ should have correct categories defined (5ms)
    ✓ Computer Hardware requires only Receipt (2ms)

Test Suites: 1 passed, 1 total
Tests:       72 passed, 72 total
```

✓ All tests passed

## Integration with Development Workflow

### Before Committing

```bash
# Run all tests
pytest && npm test

# If tests pass, commit your changes
git add .
git commit -m "Your message"
```

### Before Pushing

```bash
# Run full test suite with coverage
pytest --cov=app && npm run test:coverage

# Check coverage is adequate
# Review htmlcov/index.html for gaps
```

### When Tests Fail

1. **Identify which tests failed**
   - Check pytest or Jest output
   - Note the failing test name and error message

2. **Reproduce the failure**
   - Run just that test with verbose output
   - Check the assertion that failed

3. **Fix the issue**
   - Modify the code (not the test)
   - Unless the test itself is wrong, then fix test

4. **Verify the fix**
   - Re-run the failing test
   - Run full suite to ensure no regressions

## Performance Tips

### Speed Up Tests

```bash
# Run only file requirement tests (fastest)
pytest tests/test_file_requirements.py

# Run JavaScript tests in parallel
npm test -- --maxWorkers=4

# Run only tests related to your changes
pytest -k "direct_pay"
npm test -- --testNamePattern="Direct Pay"
```

### Parallel Execution

```bash
# Python tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# JavaScript tests already run in parallel with Jest
npm test
```

## Environment Variables

For integration testing with actual services (optional):

```bash
# Set test configuration
export TEST_ENV=test
export TEST_DB_URL=sqlite:///test.db

# Run tests
pytest
```

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Flask Testing](https://flask.palletsprojects.com/testing/)
