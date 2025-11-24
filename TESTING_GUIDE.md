# Testing Guide for ESA-Helpers

## Quick Start

### 1. Start the Application

```bash
uv run main.py
```

You should see:
```
============================================================
ESA Helper - ClassWallet Automation Tool
============================================================

Starting Flask application...
Open your browser and navigate to: http://127.0.0.1:5000

Press Ctrl+C to stop the server
```

A Chrome browser should automatically open to `http://127.0.0.1:5000`

### 2. Initial Setup

On first load, you'll see a credentials alert. Click "Configure Credentials" and enter:
- **Email:** Your ClassWallet email
- **Password:** Your ClassWallet password

These are saved locally in `config.json`.

## Testing Workflow

### Test 1: Simple Reimbursement (5 minutes)

**Purpose:** Verify basic workflow is working

**Steps:**

1. **Fill Form:**
   - Student: Select "Student B"
   - Request Type: "Reimbursement"
   - Store/Vendor Name: "Test Store"
   - Amount: "$50.00"
   - Expense Category: "Curriculum"
   - Comment: "Test submission"

2. **Skip Files (for now):**
   - We'll test file uploads separately

3. **Review and Submit:**
   - Click "Review & Submit"
   - Check confirmation modal
   - Click "Submit to ClassWallet"

4. **Monitor Terminal:**
   - Watch for these checkpoints:
     - `=== STEP 1: SELECT STUDENT ===`
     - `=== STEP 2: START REIMBURSEMENT ===`
     - `=== STEP 3: UPLOAD FILES ===`
     - `=== STEP 4: SELECT PURSE AND CATEGORY ===`
     - `=== STEP 5: FILL PO AND COMMENT ===`
     - `=== STEP 6: SUBMIT REIMBURSEMENT ===`

5. **Document Any Errors:**
   - If a step fails, copy the error message from terminal
   - Include the step number and error details in your response

### Test 2: Template-Based Reimbursement (5 minutes)

**Purpose:** Verify template system works

**Steps:**

1. **Load Template:**
   - Student: "Student B"
   - Template dropdown: Select "Lesson - Instructor A - Student B"
   - Form should auto-fill with template data

2. **Verify Auto-fill:**
   - Store Name should be: "Instructor"
   - Amount should be: "$45.00"
   - Category should be: "Tutoring & Teaching Services - Accredited Individual"
   - Comment should have date placeholder replaced

3. **Monitor File Paths:**
   - Check if Receipt/Invoice/Attestation files are found
   - Look for logging: "✓ Found {file_type}: {path}"

### Test 3: File Upload (5 minutes)

**Purpose:** Verify file selection and upload works

**Steps:**

1. **Add Files Manually:**
   - Click file type button (e.g., "Receipt")
   - File browser modal opens
   - Navigate to file location
   - Select a file
   - Verify in form

2. **Verify in Terminal:**
   - Look for: `=== STEP 3: UPLOAD FILES ===`
   - Each file should show: `✓ Found {file_type}: {absolute_path}`

### Test 4: Direct Pay (5 minutes)

**Purpose:** Verify direct pay workflow

**Steps:**

1. **Fill Form:**
   - Student: "Student A"
   - Request Type: "Direct Pay"
   - Store/Vendor Name: "Test Vendor"
   - Amount: "$100.00"
   - Expense Category: Select one
   - Comment: "Test direct pay"

2. **Submit:**
   - Follow same steps as reimbursement test

3. **Monitor Terminal:**
   - Look for: `=== STEP 2: START DIRECT PAY ===`
   - Workflow should be same except for vendor selection

## Debugging - What to Look For

### ✓ Success Indicators

When each step completes successfully, you'll see:
```
✓ Menu opened
✓ 'Switch to user' clicked
✓ Student {name} selected
```

### ❌ Error Indicators

When a step fails:
```
❌ Error selecting category: {error message}
Full traceback: {detailed error}
```

### Common Issues and Solutions

#### Issue: "Cannot find element" during STEP 1

**What:** Student selection menu not found
- Check ClassWallet is loaded
- Verify menu button is visible in browser
- Wait longer for page to fully load

**Solution:** Provide screenshot of current screen

#### Issue: Amount entry fails (STEP 2)

**What:** "Cannot find element for amount field"
- Amount field selector may have changed
- Provide HTML from form page

**Solution:** Right-click on amount field → Inspect → Copy HTML

#### Issue: File upload times out (STEP 3)

**What:** Files don't appear in form
- File paths may be incorrect
- File browser may not be opening correctly
- ClassWallet may be rejecting file format

**Solution:**
- Verify file paths exist: `ls -la /path/to/file`
- Check file permissions: `ls -l` output
- Try uploading different file type

#### Issue: Category selector fails (STEP 4)

**What:** Cannot find expense category
- Category name in form may not match ClassWallet exactly
- HTML structure may have changed

**Solution:** Provide HTML from category selection page

#### Issue: PO/Comment step not found (STEP 5)

**What:** Automation runs but doesn't fill PO and comment
- Selectors are placeholders and need validation
- Page structure may be different

**Solution:** Provide HTML from PO/comment page

#### Issue: Submit fails (STEP 6)

**What:** Submit button not found
- Using fallback selector strategy
- Button may have different attributes

**Solution:** Provide HTML from final review page

## Collecting Error Information

When you hit an error, please provide:

### 1. Terminal Output

Copy the entire terminal output from the error:

```
uv run main.py
# [Full output including error]
```

### 2. Browser Screenshots

Take a screenshot showing:
- Current page URL
- Form state/what's visible
- Any error messages on page

### 3. HTML for Problematic Page

When a selector fails:
1. Open browser DevTools: `F12` or `Cmd+Opt+I`
2. Go to Inspector/Elements tab
3. Right-click on relevant form element
4. Select "Inspect" or "Copy" → "Copy outer HTML"
5. Paste in your response with context like:
   - "This is the Amount field at STEP 2"
   - "This is the Submit button at STEP 6"

## Expected Outcomes

### Successful Test Flow

```
=== STEP 1: SELECT STUDENT ===
✓ Menu opened
✓ 'Switch to user' clicked
✓ Student Student B selected
Student selection complete!

=== STEP 2: START REIMBURSEMENT ===
✓ Found 'Start a new Reimbursement' button
✓ Entered store name: Instructor
✓ Entered amount: $45 ($4500 cents)
✓ Clicked Next button

=== STEP 3: UPLOAD FILES ===
✓ Found Receipt: /path/to/esa/student_b/2025/receipt.pdf
✓ Found Invoice: /path/to/esa/student_b/2025/invoice.pdf
✓ Sent file paths to input
✓ Next button clicked

=== STEP 4: SELECT PURSE AND CATEGORY ===
✓ Arizona - ESA already selected
✓ Category 'Tutoring & Teaching Services - Accredited Individual' selected
✓ Next button clicked

=== STEP 5: FILL PO AND COMMENT ===
✓ Entered PO number: 20250101_1430
✓ Entered comment: Lesson - Instructor A lesson - 2025-01-01
✓ Next button clicked

=== STEP 6: SUBMIT REIMBURSEMENT ===
✓ Submit button clicked
✓ Reimbursement submitted successfully

[Browser shows success modal]
```

### Expected Next Steps

After successful submission:
1. Browser shows "Submission Successful" modal
2. Modal shows the PO number
3. ClassWallet dashboard shows new submission

## Parameters to Note

- **Student Wait:** 1 second between steps (adjust if pages load slowly)
- **File Processing:** 4 seconds after upload (may need increase if slow network)
- **Element Timeout:** 10 seconds (increase in line 51 of classwallet.py if needed)
- **WebDriver Timeout:** 10 seconds per element (same as above)

## Before Running Tests

1. ✅ Verify Chrome is installed and accessible
2. ✅ Verify ClassWallet login credentials are correct
3. ✅ Verify file paths in templates actually exist
4. ✅ Check internet connection is stable
5. ✅ Close other browser windows to avoid interference

## Test Order Recommended

1. **Test 1: Simple Reimbursement** (basic flow)
2. **Test 2: Template-Based** (template system)
3. **Test 3: File Upload** (file handling)
4. **Test 4: Direct Pay** (alternative workflow)

## Next Phase: Selector Updates

Once you identify which selectors need updating:

1. Provide HTML from problematic page
2. I'll identify correct selectors
3. Update classwallet.py with new selectors
4. Re-run test to verify fix
5. Repeat until all steps pass

## Performance Notes

Each submission takes approximately:
- Student selection: 3-4 seconds
- Form filling: 2-3 seconds
- File upload: 4-6 seconds
- Category selection: 1-2 seconds
- PO and comment: 1-2 seconds
- Final submission: 2-3 seconds
- **Total: ~15-20 seconds per submission**

(Faster than manual 35-40 minutes!)

## Questions?

Reference the IMPLEMENTATION_STATUS.md for:
- Technical architecture
- List of completed features
- Known issues
- File structure
