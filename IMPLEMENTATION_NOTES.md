# Implementation Notes - ClassWallet Automation

## Important: Selector Verification Required

The Selenium selectors in `app/classwallet.py` are based on typical HTML patterns and the workflow described. **These selectors MUST be verified and adjusted based on the actual ClassWallet HTML structure.**

## How to Update Selectors

### 1. Inspect ClassWallet Forms

When you run the automation:
1. Watch the browser as it submits
2. Right-click on elements and select "Inspect" (or F12)
3. Note the actual HTML structure
4. Update selectors in `app/classwallet.py` if they don't match

### 2. Common Selector Types

```python
# By ID
element = driver.find_element(By.ID, "elementId")

# By Name (form fields often use this)
element = driver.find_element(By.NAME, "fieldName")

# By CSS Selector
element = driver.find_element(By.CSS_SELECTOR, ".class-name")

# By XPath (most flexible, but fragile)
element = driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
```

### 3. Likely Selectors That Need Verification

In `app/classwallet.py`, these selectors should be verified and updated:

**Student Dropdown Selection**
```python
# Current: TODO placeholder
# Likely actual selector patterns:
# - <select id="studentSelect"> or similar
# - <button class="student-picker">
# - Click dropdown, then select option
```

**Reimbursement Start Button**
```python
# Current XPath:
button = driver.find_element(By.XPATH, "//button[contains(text(), 'Start a new Reimbursement')]")

# If button text differs, update this
# Check actual text in ClassWallet
```

**Form Field Names**
```python
# These need verification:
store_field = driver.find_element(By.NAME, "storeName")
amount_field = driver.find_element(By.NAME, "amount")
po_field = driver.find_element(By.NAME, "poNumber")
comment_field = driver.find_element(By.NAME, "comment")

# Actual names in ClassWallet may differ
```

**Expense Category Dropdown**
```python
# Current pattern:
category_dropdown = driver.find_element(By.NAME, "expenseCategory")
category_option = driver.find_element(By.XPATH, f"//option[contains(text(), '{category}')]")

# ClassWallet may use different approach:
# - Custom select component
# - React/Vue component
# - Different naming convention
```

**Arizona ESA Checkbox**
```python
# Current:
esa_checkbox = driver.find_element(By.NAME, "arizonaESA")

# Verify actual checkbox name/id
```

## Debugging Strategy

### Step 1: Add Debug Output

In `app/classwallet.py`, add logging at critical points:

```python
def start_reimbursement(self, store_name: str, amount: str):
    try:
        logger.info(f"Looking for reimbursement button...")

        # Add this to see what's on the page
        logger.info(f"Current URL: {self.driver.current_url}")
        logger.info(f"Page title: {self.driver.title}")

        # Try to find the button
        reimbursement_button = self.wait.until(...)
```

### Step 2: Manual Browser Inspection

1. Run the automation with `python main.py`
2. Submit a test form
3. When browser opens, let it run
4. If it stops, press F12 to open Developer Tools
5. Find the element it's looking for
6. Copy the correct selector
7. Update the code

### Step 3: Print Page HTML

Add this to debug a specific step:

```python
# Add to classwallet.py to print page HTML
logger.info(self.driver.page_source)
```

This shows the entire page source when a step fails.

## Common Issues & Fixes

### Issue: Element not found with timeout

```python
# Error: TimeoutException waiting for element

# Solution: Increase wait time
self.wait = WebDriverWait(self.driver, 20)  # Increase from 10 to 20 seconds

# Or: Check if element exists with different selector
try:
    element = driver.find_element(By.NAME, "storeName")
except:
    # Try alternative selector
    element = driver.find_element(By.XPATH, "//input[@placeholder='Store Name']")
```

### Issue: Stale element reference

```python
# Error: Element is no longer attached to DOM

# Solution: Wait for element again after navigation
self.wait.until(EC.presence_of_element_located((By.NAME, "fieldName")))
element = self.driver.find_element(By.NAME, "fieldName")
```

### Issue: File upload not working

```python
# Some file inputs may be hidden
file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")

# Try sending keys directly
file_input.send_keys("/full/path/to/file.pdf")

# If still not working, try JavaScript
driver.execute_script("arguments[0].style.display = 'block';", file_input)
```

## Testing Workflow

### Phase 1: Manual Verification
1. Open ClassWallet manually
2. Complete one submission manually
3. Note exact HTML structure
4. Document all field names and button texts

### Phase 2: Update Selectors
1. Edit `app/classwallet.py` with correct selectors
2. Add logging statements
3. Update wait strategies if needed

### Phase 3: Test Automation
1. Run `python main.py`
2. Fill out form with test data
3. Submit and watch browser automation
4. Check logs in `logs/` directory
5. Verify submission in ClassWallet

### Phase 4: Refine
1. Fix any selector issues found
2. Adjust timeouts if needed
3. Test multiple submissions
4. Test different expense categories
5. Test Direct Pay workflow

## Known Limitations

### SAML Authentication
The app logs in via ESA Portal which uses SAML. If ClassWallet changes their login method:
- Update `login_to_classwallet()` in classwallet.py
- The workflow may require different authentication

### Dynamic Content
If ClassWallet uses JavaScript to render forms:
- May need to wait for JavaScript execution
- Use `WebDriverWait` with custom conditions
- Consider using `driver.execute_script()` for JavaScript interactions

### Vendor Search (Direct Pay)
The vendor search implementation assumes:
- A text input field for search
- Search results appear below
- Clicking a result selects it

If ClassWallet uses different approach:
- May need to scroll through dropdown
- May need to use arrow keys to navigate
- May need to wait for AJAX results

## File Upload Handling

**Current implementation**:
```python
file_input.send_keys(str(Path(file_path).absolute()))
```

**If this doesn't work**:
- ClassWallet may use drag-and-drop
- May require clicking "Browse" button first
- May use iframe or shadow DOM
- Try JavaScript method:

```python
# Upload via JavaScript
js_code = f"""
var input = document.querySelector('input[type="file"]');
var file = new File([''], '{file_name}');
var event = new DataTransfer();
event.items.add(file);
input.files = event.files;
input.dispatchEvent(new Event('change', {{ bubbles: true }}));
"""
driver.execute_script(js_code)
```

## Category Selection

The expense category text must match EXACTLY what appears in ClassWallet:

From ESA_WORKFLOW.md:
```
1. Computer Hardware & Technological Devices
2. Curriculum
3. Tutoring & Teaching Services – Accredited Facility/Business
4. Tutoring & Teaching Services – Accredited Individual
5. Supplemental Materials (Curriculum Always Required)
```

**Important**: Check if ClassWallet uses:
- Em dashes (–) or hyphens (-)
- Different capitalization
- Different full name

If they differ, update in:
1. `app/routes.py` - expense_categories dictionary
2. `app/templates/index.html` - dropdown options
3. `app/classwallet.py` - category_option selector

## PO Number Handling

Current approach:
1. Generate on frontend
2. Send to backend
3. Fill in ClassWallet

If ClassWallet auto-generates PO numbers:
- You may need to skip this step
- Or override auto-generated with your own
- Check if there's a "Clear" or "Generate" button

## Comment Field

Current format: `AZ [Activity] - YYYY-MM-DD`

If ClassWallet has character limits:
- Truncate comment if needed
- Update validation in `app.js`

## Student Selection

Current implementation assumes:
- Dropdown selector for students
- Students identifiable by name

If ClassWallet requires student ID:
- Update `config.json` with student IDs
- Modify `select_student()` to use IDs instead of names
- Update routes to fetch student IDs

## Browser Headless Mode

Development should use `headless=False` to watch automation:

```python
automation = ClassWalletAutomation(
    email=email,
    password=password,
    headless=False  # See the browser action
)
```

For production/scheduled runs, can use `headless=True`:
```python
headless=True  # No browser window
```

## Error Handling

Current error handling logs to:
- Console output (development)
- `logs/` directory (submission records)

For better debugging:
1. Check terminal output during automation
2. Check `logs/submission_*.json` files
3. Look for `ERROR` log messages

Example log file: `logs/submission_20241103_143022.json`

## Next Steps for Integration

1. **Verify Selectors**: Go through ClassWallet and verify all selectors
2. **Test Login**: Ensure SAML login still works
3. **Test Each Step**: Test each automation method independently
4. **Full Test**: Test complete submission workflow
5. **Different Categories**: Test each expense category
6. **Direct Pay**: Test Direct Pay workflow with vendor selection
7. **Error Cases**: Test error handling (missing files, timeout, etc.)

## Troubleshooting Checklist

- [ ] Verify all XPath expressions match actual HTML
- [ ] Check field names in forms (use inspector)
- [ ] Verify button text (may have spaces or special chars)
- [ ] Confirm category names match exactly
- [ ] Test file upload with different file types
- [ ] Verify student dropdown works correctly
- [ ] Test with credentials that have multiple accounts
- [ ] Check for session timeout during submission
- [ ] Verify file paths are absolute (not relative)
- [ ] Test with large files (>10MB)

## Quick Reference: Key Code Locations

| Task | File | Method |
|------|------|--------|
| Login logic | classwallet.py | `login_to_classwallet()` |
| Student selection | classwallet.py | `select_student()` |
| Start reimbursement | classwallet.py | `start_reimbursement()` |
| File upload | classwallet.py | `upload_files()` |
| Category selection | classwallet.py | `select_expense_category()` |
| Submission | classwallet.py | `submit_reimbursement()` |
| Orchestration | automation.py | `SubmissionOrchestrator` |
| API routes | routes.py | `/api/*` |
| Form HTML | templates/index.html | Form fields |
| Form JS | static/js/app.js | Form logic |

---

**Remember**: The selectors are the bridge between your form and ClassWallet. Getting them right is critical for reliability!
