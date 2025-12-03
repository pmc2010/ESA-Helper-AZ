# Manual Entry Feature Documentation

## Overview

The Manual Entry feature allows users to log ESA (Empowerment Scholarship Account) transactions that were not processed through the ClassWallet automation tool. This enables accurate budget tracking for transactions completed outside the automated workflow.

**Added**: December 2, 2025

## Features

### 1. Manual Transaction Logging
- Log transactions without ClassWallet automation
- No file uploads required
- Specify transaction date for historical entries
- Same expense categories as automated submissions
- Full edit and delete capability

### 2. Form UI
**Location**: Main submission form (`/`)

**New "Entry Type" Card**:
- Toggle checkbox: "Manual Entry - Log a transaction without automation"
- Hidden by default, shows only when toggled
- When enabled:
  - Hides file upload section
  - Hides invoice generation section
  - Shows "Transaction Date" date picker field

**Form Fields Required**:
- Student (required)
- Request Type: Reimbursement or Direct Pay (required)
- Store/Vendor Name (required)
- Amount (required, > $0)
- Expense Category (required)
- **Transaction Date** (required for manual entries)
- PO Number (required)
- Comment (optional)

**Button Text**:
- Automated submission: "Review & Submit"
- Manual entry: "Log Transaction"

### 3. Submission History Filtering
**Location**: Submission History page (`/submission-history`)

**Filter Controls**:
- All Submissions (default)
- Automated Only (hides manual entries)
- Manual Only (shows manual entries only)

**Visual Indicators**:
- Manual entries have a gray left border
- Badge: "Manual Entry" in gray
- Automated entries show type badge: "Reimbursement" or "Direct Pay"

**Detail View**:
- Shows "Manual Entry" as the type
- Displays transaction date
- Shows all submission details

### 4. Reports Integration
**Location**: Reports & Analytics page (`/reports`)

**Integration**:
- Manual entries are included in all calculations
- Month-by-month spending totals include manual entries
- YTD (Year-to-Date) calculations include manual entries
- Annualized rate calculations include manual entries
- Budget comparison includes manual entries

## Technical Implementation

### Backend API Endpoints

#### POST `/api/manual-submission`
**Purpose**: Create a new manual transaction entry

**Request Payload**:
```json
{
  "student": "Student Name",
  "request_type": "Reimbursement|Direct Pay",
  "store_name": "Vendor Name",  // for Reimbursement
  // OR
  "vendor_name": "Vendor Name",  // for Direct Pay
  "amount": "45.50",
  "expense_category": "Category Name",
  "po_number": "PO-2025-001",
  "comment": "Transaction notes",
  "entry_date": "2025-11-15",
  "source": "manual"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Manual transaction logged successfully",
  "po_number": "PO-2025-001"
}
```

**Status Codes**:
- 201: Created successfully
- 400: Missing required fields
- 500: Server error

#### PUT `/api/manual-submission/{po_number}`
**Purpose**: Update an existing manual transaction entry

**Editable Fields**:
- amount
- expense_category
- comment
- vendor_name (for Direct Pay)
- store_name (for Reimbursement)

**Non-editable Fields** (preserved):
- timestamp
- logged_at
- source
- entry_date

**Response**:
```json
{
  "success": true,
  "message": "Manual submission updated successfully",
  "submission": { /* updated submission data */ }
}
```

#### DELETE `/api/manual-submission/{po_number}`
**Purpose**: Delete a manual transaction entry

**Response**:
```json
{
  "success": true,
  "message": "Manual submission deleted successfully"
}
```

### Data Storage

**Location**: `logs/submission_history.json`

**Structure**:
```json
{
  "type": "manual_entry",
  "source": "manual",
  "student": "Allie Curtis",
  "request_type": "Reimbursement",
  "store_name": "Ice Skating Rink",
  "amount": 45.50,
  "expense_category": "Tutoring & Teaching Services - Accredited Individual",
  "po_number": "PO-2025-001",
  "comment": "Skating lesson with Katlynn",
  "entry_date": "2025-11-15",
  "logged_at": "2025-12-02T15:30:45.123Z",
  "timestamp": "20251202_153045",
  "created_by": "manual"
}
```

## Testing

### Manual Testing Guide

#### Test 1: Basic Manual Entry Submission
1. Navigate to `/` (main form)
2. Select student "Allie Curtis"
3. Select request type "Reimbursement"
4. Enter store name: "Ice Skating Rink"
5. Enter amount: "45.50"
6. Select category: "Tutoring & Teaching Services - Accredited Individual"
7. **Check "Manual Entry" checkbox**
8. Select transaction date: "2025-11-15"
9. Enter PO number (auto-generated or custom)
10. Enter comment: "Skating lesson"
11. Click "Log Transaction" button
12. Verify success modal appears with message "Transaction Logged"
13. Verify no browser automation occurs (no ClassWallet interaction)

**Expected Result**: ✓ Manual entry appears in submission history

#### Test 2: Manual Entry in Submission History
1. Navigate to `/submission-history`
2. Look for the manually created entry
3. Verify:
   - Gray left border (not blue/teal)
   - "Manual Entry" badge in gray
   - Correct student and vendor names
   - Correct amount and date

**Expected Result**: ✓ Manual entry displays correctly with proper styling

#### Test 3: Manual Entry Filtering
1. Navigate to `/submission-history`
2. Test filter: "Automated Only"
   - Manually created entry should disappear
3. Test filter: "Manual Only"
   - Only manually created entries should show
4. Test filter: "All Submissions"
   - Both manual and automated entries should show

**Expected Result**: ✓ Filters work correctly

#### Test 4: Manual Entry in Reports
1. Navigate to `/reports`
2. Select month that contains manual entry (e.g., November 2025)
3. Click "Load Analytics"
4. Verify:
   - Student's total spending includes manual entry amount
   - YTD total includes manual entry amount
   - Annualized rate reflects manual entry

**Expected Result**: ✓ Manual entries are included in all calculations

#### Test 5: Edit Manual Entry
1. Go to submission history
2. Click on a manual entry to view details
3. Delete the entry by clicking delete button
4. Confirm deletion in dialog

**Expected Result**: ✓ Manual entry is removed

**Note**: Edit functionality is available via API (PUT endpoint) but not yet exposed in the UI

#### Test 6: Validation
1. Check "Manual Entry" checkbox
2. Verify "Transaction Date" field appears
3. Try to submit without selecting a date
4. Verify "Log Transaction" button remains disabled
5. Select a date
6. Verify "Log Transaction" button enables

**Expected Result**: ✓ Form validation requires transaction date for manual entries

### Automated Testing

Currently, automated tests for manual entry feature are not yet implemented. To add tests:

1. **Create** `tests/test_manual_entry.py`
2. **Test cases needed**:
   - POST `/api/manual-submission` with valid data
   - POST `/api/manual-submission` with missing required fields
   - PUT `/api/manual-submission/{po_number}` to update entry
   - DELETE `/api/manual-submission/{po_number}` to remove entry
   - Verify manual entries appear in submission history
   - Verify manual entries included in reports calculations

### Console Validation

When testing, check the Browser Console (F12) for validation logs:

**For Manual Entry Enabled**:
```
Form Validation Debug:
  Manual Entry: ✓ ENABLED
  Entry Date: ✓ FILLED (2025-11-15)
  Overall Valid: true
  Button Disabled: false
```

**For Manual Entry with Missing Date**:
```
Form Validation Debug:
  Manual Entry: ✓ ENABLED
  Entry Date: ✗ EMPTY
  Overall Valid: false
  Button Disabled: true
```

## Files Modified

### Backend
- `app/routes.py`
  - Added `POST /api/manual-submission` endpoint (lines 976-1034)
  - Added `PUT /api/manual-submission/<po_number>` endpoint (lines 1037-1094)
  - Added `DELETE /api/manual-submission/<po_number>` endpoint (lines 1097-1127)
  - Improved `GET /api/config/credentials` validation (lines 665-676)

### Frontend HTML
- `app/templates/index.html`
  - Added "Entry Type" card with manual entry toggle (lines 197-218)
  - Added "Transaction Date" date picker field (lines 212-216)

- `app/templates/submission-history.html`
  - Added filter controls (lines 122-135)
  - Added manual entry badge styling (lines 69-73)
  - Updated displaySubmissions() to show manual badge (line 296)
  - Updated createSummaryRow() to handle manual entries
  - Updated detail modal to show entry_date (lines 384-389)

- `app/templates/manage-students.html`
  - Added favicon link

- `app/templates/reports.html`
  - Added favicon link

### Frontend JavaScript
- `app/static/js/app.js`
  - Enhanced validateForm() with manual entry validation (lines 196-207, 243-244)
  - Updated toggleManualEntry() to show/hide date field (lines 267-304)
  - Updated confirmSubmit() to route to correct endpoint (lines 1253-1261)
  - Added event listeners for entry date field (lines 339-344)
  - Added safety checks for null elements (lines 196-199)
  - Updated debug logging for validation

### Static Assets
- `app/static/favicon.ico`
  - New professional favicon with ESA branding

## Browser Compatibility

Tested on:
- Chrome 120+ ✓
- Safari 17+ ✓
- Firefox 121+ ✓

**Note**: Date input (`<input type="date">`) requires HTML5 support, available in all modern browsers.

## Known Limitations

1. **Edit UI**: Manual entries can be edited via API but not through the web interface
2. **Bulk Operations**: No bulk edit/delete for multiple manual entries
3. **Validation**: Client-side validation only; server-side validation could be enhanced
4. **Audit Trail**: No change history for edited manual entries

## Future Enhancements

- [ ] UI for editing manual entries in submission history
- [ ] Bulk delete for multiple manual entries
- [ ] Manual entry templates for recurring transactions
- [ ] Import/export manual entries as CSV
- [ ] Change audit trail for edited entries
- [ ] Batch manual entry import from spreadsheet
- [ ] Manual entry categories (different from automated)

## Support & Troubleshooting

### Button Stays Disabled After Selecting Date
**Solution**: Hard refresh the page (Cmd+Shift+R on Mac) to ensure latest JavaScript loads

### Transaction Date Field Not Visible
**Solution**: Ensure "Manual Entry" checkbox is checked. The date field is hidden until toggled.

### Manual Entry Not Appearing in Reports
**Solution**:
1. Ensure the entry date falls within the selected month in reports
2. Verify the transaction was successfully logged (check submission history)
3. Hard refresh the reports page

### API Error "Missing required fields"
**Solution**: Verify all required fields are present in request:
- student
- request_type
- store_name (for Reimbursement) or vendor_name (for Direct Pay)
- amount
- expense_category
- po_number
- comment (can be empty string)
- entry_date

## Related Documentation

- [README.md](README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - User guide
- [TESTING.md](TESTING.md) - Complete testing guide
- [CLAUDE.md](CLAUDE.md) - Developer documentation
