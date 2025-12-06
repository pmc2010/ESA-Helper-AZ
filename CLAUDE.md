# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

**What this tool does**: Automates ESA (Education Savings Account) reimbursement submissions and direct vendor payments in ClassWallet, reducing 35-40 minutes of manual form-filling to 5-25 minutes via browser automation.

**Tech stack**: Flask backend + Vanilla JavaScript frontend + Selenium browser automation + JSON data storage.

**Key file to start with**: `main.py` → `app/automation.py` → `app/classwallet.py` (shows the workflow in order).

## ⚠️ CRITICAL: Public Repository - Privacy Protection

**THIS IS A PUBLIC GITHUB REPOSITORY.** All commits and files are publicly visible.

### Privacy Rules (MUST FOLLOW)

**NEVER create, commit, or modify files containing:**
- Real student names, family member names, or personal identities
- Actual vendor names, business names, or contact information
- Real addresses, phone numbers, or email addresses
- Actual ClassWallet credentials, API keys, or passwords
- Real financial data, account numbers, or transaction IDs
- Screenshots or documents containing personal information
- Any other personally identifiable information (PII)

### Safe Practices

**When creating test files:**
- Use generic names: "Test Student A", "Test Student B", "Test Vendor LLC"
- Use placeholder data: "123 Test St", "test@example.com", "555-1234"
- Use fictional amounts and dates
- Never reference real people or businesses

**When writing documentation:**
- Use examples with fictional data only
- Redact any real information before committing
- Avoid specific implementation details that reveal personal use patterns

**Files already git-ignored (safe for personal data):**
- `config.json` - ClassWallet credentials
- `data/students.json` - Student profiles
- `data/vendors.json` - Vendor profiles
- `data/esa_templates/` - Template data
- `logs/` - Submission history

**If personal information was accidentally committed:**
1. Do NOT just delete it in a new commit (it remains in git history)
2. Follow the GitHub guide to remove sensitive data from history
3. Force-push to overwrite the repository history
4. Rotate any exposed credentials immediately

### Code Review Checklist

Before committing ANY file, verify:
- [ ] No real names appear in code, tests, or documentation
- [ ] No real contact information (email, phone, address)
- [ ] No credentials or API keys (even expired ones)
- [ ] Sample data uses only generic/fictional information
- [ ] Screenshots or images contain no PII

## Common Commands

### Running the Application

```bash
# Start the dev server (opens browser automatically)
uv run main.py

# App runs on http://localhost:5000
# Logs go to console and logs/ directory
```

### Development Setup

```bash
# Install dependencies
uv sync

# Verify Python version (need 3.11+)
python --version

# Verify Chrome is installed (required for automation)
which google-chrome  # or 'where google-chrome' on Windows
```

### Testing

**Automated tests are now available**. See `TESTING.md` for comprehensive guide.

Quick start:
```bash
# Run all tests
./scripts/run_all_tests.sh

# Run only file requirement tests (critical for Direct Pay changes)
./scripts/test_file_requirements.sh

# Run with coverage reports
./scripts/test_coverage.sh

# Python tests
pytest tests/

# JavaScript tests
npm test
```

**Manual testing** also available:
1. Run `uv run main.py`
2. Test in browser at `http://localhost:5000`
3. Use sample data in `data/students.sample.json`, `data/vendors.sample.json`
4. Check `logs/` directory for submission records
5. Verify data saved to `data/` JSON files

### Code Quality

```bash
# Check Python syntax (all files)
python3 -m py_compile app/*.py

# No linter currently configured
# Code review recommendations in SECURITY.md and code review findings
```

## Architecture Overview

### Three-Layer Architecture

```
Frontend (HTML/CSS/JS)
    ↓ AJAX calls
API Layer (Flask routes)
    ↓ Calls
Automation Layer (Selenium + Orchestration)
    ↓ Uses
Data Layer (JSON files)
```

### Key Components

1. **`app/automation.py`** (326 lines)
   - `SubmissionOrchestrator` class coordinates multi-step workflows
   - Loads credentials, initializes browser, executes steps sequentially
   - Entry point: `submit_to_classwallet()` function

2. **`app/classwallet.py`** (953 lines - LONGEST, most critical)
   - `ClassWalletAutomation` class wraps Selenium interactions
   - 6-step workflow: login → select student → start reimbursement → upload files → select category → submit
   - **Has fallback selectors** (tries multiple CSS/XPath selectors for robustness)
   - Each step heavily logged with ✓ checkmarks
   - **Brittleness**: Selectors break when ClassWallet updates UI

3. **`app/routes.py`** (1200 lines)
   - All HTTP endpoints (main_bp for pages, api_bp for REST)
   - Main submission route: `POST /api/submit`
   - CRUD operations for students, vendors, templates
   - Invoice generation endpoint: `POST /api/invoice/generate`

4. **`app/invoice_generator.py`** (548 lines)
   - Creates Excel invoices from templates using `openpyxl`
   - Converts to PDF using LibreOffice subprocess (optional)
   - Fills template with student/vendor/invoice data

5. **`app/static/js/app.js`** (1747 lines)
   - Form validation, AJAX calls, template loading
   - File preview using Pillow-generated thumbnails
   - Modal dialogs for workflows

### Data Storage

All data is JSON (no database):
- `data/students.json` - Student profiles (name, address, folder path)
- `data/vendors.json` - Vendor profiles (name, business info, email, tax rate)
- `data/esa_templates/{student_id}.json` - Templates per student (vendor_id, amount, category)
- `config.json` - Credentials (plaintext, git-ignored)
- `logs/submission_*.json` - Submission history

**Why JSON?** Easier to backup, share, migrate than database. Trade-off: no concurrent write safety (acceptable for single user).

## Key Workflows

### Reimbursement Submission (Main Flow)

```
User fills form → POST /api/submit → SubmissionOrchestrator
→ Login to ClassWallet
→ Select student
→ Click "Start Reimbursement"
→ Fill store name & amount
→ Upload files
→ Handle image editor modal (auto-click Save)
→ Select expense category
→ Fill PO number & comment
→ Submit form
→ Log to logs/ directory
→ Close browser
→ Return success to frontend
```

Each step has extensive logging. Check console or `logs/` for debugging.

### Direct Pay Submission Workflow (New - November 2025)

```
User fills Direct Pay form → POST /api/submit → SubmissionOrchestrator
→ Login to ClassWallet
→ Select student
→ Click "Start Direct Pay"
→ Search for and select vendor (using classwallet_search_term if configured)
→ Enter amount
→ Upload files (optional)
→ Select expense category
→ Fill additional info (invoice/quote number, comments)
→ Proceed to Review page
→ Submit form (if auto_submit=True) OR leave for manual review
→ Log to logs/ directory
→ Keep browser open indefinitely for user review
→ Return success to frontend
```

**Key Differences from Reimbursement:**
- Uses vendor lookup instead of store name entry
- Optional files (no payment receipt required)
- Requires `classwallet_search_term` in vendor profile for automated lookup
- Additional info page has different field structure than reimbursement
- Browser stays open indefinitely instead of closing (for manual review/submission)

**Vendor Configuration:**
Direct Pay requires vendors to be configured with:
- `name` - Display name for user
- `classwallet_search_term` - Exact search term to find vendor in ClassWallet (required for automation)
- Other business info (email, tax rate, etc.)

If a vendor lacks `classwallet_search_term`, user cannot select it for Direct Pay and sees a clear warning.

### Invoice Generation (Optional)

```
User clicks "Request Invoice"
→ Load student & vendor profiles
→ Create Excel from template
→ Convert to PDF (LibreOffice)
→ Return download links
```

Used to create professional invoices for vendors.

### File Upload with Modal Handling

Files are uploaded via Selenium. ClassWallet sometimes shows an image editor modal with "Save" button. Code detects this and auto-clicks it.

```python
# In upload_files() method:
if not self.handle_image_editor_modal():
    return False
```

## Important Design Patterns

### Orchestration Pattern
- `SubmissionOrchestrator` coordinates multi-step workflows
- Each step depends on previous (must login before selecting student, etc.)
- Resource cleanup in finally block

### Facade Pattern
- `ClassWalletAutomation` hides Selenium complexity
- Simple methods (`login_to_classwallet()`, `select_student()`, etc.)
- Complex selectors and retry logic hidden internally

### Strategy Pattern (Selector Fallback)
- Multiple CSS/XPath selectors for same element
- Tries each in order until one works
- Increases robustness when ClassWallet UI changes
- Example: 8+ selectors for "Arizona - ESA" purse button

### Template Method
- API routes follow consistent pattern: validate → load → process → save → return JSON
- Makes routes predictable and maintainable

## Brittleness Points & Common Issues

### 1. Selectors Break When ClassWallet Updates UI
**File**: `app/classwallet.py` (especially `select_expense_category()` and `select_student()` methods)

**Solution**:
1. Open ClassWallet in browser (manually)
2. Right-click failed element → Inspect
3. Find correct CSS selector or XPath
4. Add to selector list in `classwallet.py`
5. Test with actual submission

**Fallback selectors are your friend** - always add multiple options.

### 2. File Path Issues
**Note**: Paths are configured in student profiles. Code reads from `students.json` `folder` field.

Configure your student folder paths in the "Manage Students" interface for proper file handling.

### 3. LibreOffice PDF Conversion
**Issue**: May fail silently if LibreOffice not installed.
**Solution**: Excel files still work. For PDF, user needs: `brew install libreoffice` on Mac.

### 4. Image Editor Modal Not Closing
**Issue**: If modal appears and auto-click fails, browser waits indefinitely.
**Solution**: `handle_image_editor_modal()` has 3-second timeout, so it won't hang.

## Critical Security Issues (See SECURITY.md)

1. **Plaintext Credentials** - Passwords stored in `config.json` (git-ignored)
2. **No Authentication** - Web interface has no login
3. **Path Traversal Risk** - File browser could be exploited
4. **Command Injection Risk** - Subprocess calls need to avoid shell=True

**For Family Use**: Acceptable because designed for personal, trusted computers.
**For Production**: Would need encryption, auth, input validation.

## Code Review Findings

Comprehensive code review identified:
- **8 Critical issues** (hardcoded credentials, missing auth, path traversal)
- **12 High priority** (CSRF protection, input validation, browser cleanup)
- **15 Medium priority** (error handling, logging, code duplication)

See complete review in code review notes. Top fixes: environment variables, input validation, path whitelisting.

## Important Implementation Details

### Why Selenium, Not Direct API?
ClassWallet has no public API. The tool must interact with the UI as a human would, filling forms and clicking buttons. This is why it's slow (5-25 min) compared to API calls (seconds).

### Why No Database?
Single-user, family computer. JSON files easier to backup, share, migrate. Trade-off: no concurrent write safety (acceptable).

### Why Browser Auto-Closes?
Saves resources. User can manually check ClassWallet if needed to verify submission.

### Why Multiple File Upload Formats?
Different expense categories require different files:
- Tutoring (Individual): Receipt + Invoice + Attestation
- Tutoring (Facility): Receipt + Invoice
- Supplemental Materials: Receipt + Curriculum

Code checks category and shows/requires appropriate fields.

## Testing

### Automated Test Suite (November 2025)

Comprehensive test suite with 85 passing tests covering:

**Direct Pay Workflow Tests** (`tests/test_direct_pay.py` - 7 test classes):
- Basic Direct Pay submission flow with all steps
- Search term handling from vendor configuration
- Login failure graceful degradation
- Vendor selection failures
- Submission logging with category and comment fields
- Non-auto-submit mode (stops at review for manual submission)
- PO number and comment field filling

**Submission Logging Tests** (`tests/test_submission_logging.py` - 10 test classes):
- Submission entry creation with all fields
- Category and comment inclusion in logs
- Master history file updates
- Optional field handling
- History sorting (newest first)
- Direct Pay vs Reimbursement specific logging
- Missing optional fields graceful handling

### Running Tests

```bash
# Run all pytest tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_direct_pay.py -v

# Run specific test
pytest tests/test_direct_pay.py::TestDirectPayWorkflow::test_direct_pay_submission_basic_flow -v
```

### Test Coverage (November 2025)

Current coverage: 23% overall (85 tests passing)

Key tested areas:
- Direct Pay submission orchestration
- Submission history logging with all fields
- Vendor configuration validation

### Before Making Changes

Always run automated tests to establish a baseline:
```bash
# Install test dependencies
uv sync

# Run all tests with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test New Selector
```python
# In classwallet.py, try new selector before adding to main code
try:
    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "new-selector")))
    logger.info("✓ Found element with new selector")
except:
    logger.error("Selector didn't work")
    return False
```

### Test Submission Flow Locally
1. Use sample data: `cp data/students.sample.json data/students.json`
2. Configure credentials (even fake ones for testing)
3. Run: `uv run main.py`
4. Fill form with test data
5. Check logs/ for submission record

### Test Invoice Generation
```
1. Ensure student folder exists
2. Click "Request Invoice"
3. Check logs/ for any errors
4. Verify .xlsx file created in student folder
```

### After Making Changes
1. Run `./scripts/run_all_tests.sh` to verify no regressions
2. Check coverage with `./scripts/test_coverage.sh`
3. Test manually to ensure UI works as expected
4. Commit only if all tests pass

## File Organization Notes

```
ESA-Helper-AZ/
├── main.py                          # Entry point - start here
├── app/
│   ├── __init__.py                 # Flask app factory (create_app())
│   ├── routes.py                   # All HTTP endpoints
│   ├── automation.py               # Workflow orchestration
│   ├── classwallet.py              # Selenium browser automation
│   ├── invoice_generator.py        # Excel/PDF generation
│   ├── utils.py                    # Shared utilities
│   ├── templates/                  # HTML pages
│   └── static/                     # CSS/JavaScript
├── data/
│   ├── students.json              # User data (git-ignored)
│   ├── vendors.json               # User data (git-ignored)
│   ├── esa_templates/             # User templates (git-ignored)
│   └── *.sample.json              # Templates for new users
├── logs/                           # Submission records
├── config.json                     # Credentials (git-ignored)
├── CLAUDE.md                       # This file
├── SETUP.md                        # Initial setup guide
├── SECURITY.md                     # Security considerations
└── README.md                       # Overview
```

## Code Review & Documentation

**Before deploying changes**:
1. Review SECURITY.md for known limitations
2. Check if new endpoints need input validation
3. Verify logs are not exposing sensitive data
4. Test with sample data first

**Important files documenting the system**:
- `README.md` - Overview, features, limitations
- `SETUP.md` - How to set up for sharing
- `SECURITY.md` - Security posture and best practices
- `QUICKSTART.md` - User guide
- `ESA_WORKFLOW.md` - Detailed workflow documentation (if exists)

## Dependencies

**Critical**:
- `selenium >= 4.38.0` - Browser automation
- `flask >= 3.0.0` - Web framework
- `openpyxl >= 3.1.0` - Excel file creation
- `pillow >= 10.0.0` - Image handling

**Optional**:
- `reportlab >= 4.0.0` - PDF generation (fallback)
- LibreOffice - PDF conversion (system-level)

**External Requirements**:
- Python 3.11+
- Chrome browser
- (Optional) LibreOffice for Excel→PDF

## Next Steps for New Work

1. **Understand the workflow first**: Read through `automation.py` and `classwallet.py` sequentially
2. **Check if it's a selector issue**: If something breaks, it's likely ClassWallet UI changed
3. **Look at logs**: Both console logs and `logs/` directory JSON files contain debugging info
4. **Test with sample data**: Don't use real credentials/data while developing
5. **Review SECURITY.md** before making any auth/credential changes
6. **Check code review findings** in conversation history for known issues

## Recent Updates

### November 2025 - Direct Pay Automation Complete
- ✓ Full Direct Pay submission workflow implemented and tested
- ✓ Vendor search term configuration for automated lookup
- ✓ Additional info page handling (comments, invoice/quote numbers)
- ✓ Browser keeps open indefinitely for user review
- ✓ Submission logging includes category and comment fields
- ✓ 17 new tests for Direct Pay workflow and logging (7 + 10)
- ✓ Documentation updated with Direct Pay workflow details
- See README.md for Direct Pay usage instructions

### November 2025 - Template Feature Implementation
- ✓ Dynamic file path selection UI for templates
- ✓ Save template functionality implemented (replaced "coming soon")
- ✓ Delete template functionality working
- ✓ 19 new tests for template CRUD operations
- See TEMPLATE_FEATURE_SUMMARY.md for details

### November 2025 - Testing Infrastructure
- ✓ Comprehensive test suite (85 tests, all passing)
- ✓ Python unit and integration tests with pytest
- ✓ Code coverage reporting (23% overall)
- ✓ Test coverage for Direct Pay and submission logging
- See tests/ directory for all test files

### Earlier - Direct Pay File Requirements
- ✓ Implemented invoice-only requirements for Direct Pay
- ✓ Optional curriculum and receipt handling
- ✓ Dynamic UI that updates based on request type

## Last Updated

November 2025 - Direct Pay automation complete with full testing coverage (85 tests, 23% code coverage)

---

For detailed architecture and workflow diagrams, see the comprehensive analysis generated during codebase review.
