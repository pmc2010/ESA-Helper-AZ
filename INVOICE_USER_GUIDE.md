# Invoice Generation Feature - User Guide

## Overview

The invoice generation feature automatically creates professional Excel and PDF invoices for your ESA reimbursements. This saves 5-10 minutes per submission by eliminating manual invoice creation in Excel.

## How to Use

### Step 1: Fill Basic Form Information

Start with the standard form fields:
- **Student:** Select student (Student A, Student B, or Student C)
- **Request Type:** Reimbursement or Direct Pay
- **Store/Vendor Name:** Vendor name (e.g., "Instructor")
- **Amount:** Payment amount (e.g., 45.00)
- **Expense Category:** Select category
- **PO Number:** Generate or enter
- **Comment:** Note about transaction

### Step 2: Enable Invoice Generation

Check the checkbox: **"Generate invoice for this transaction"**

The Invoice Generation section will expand, showing:
- Vendor Name (auto-filled from Store/Vendor Name)
- Student Name (auto-filled from Student selection)
- Invoice Number (auto-filled from PO Number, can override)
- Invoice Date (defaults to today)
- Description (can be customized)
- Quantity (defaults to 1)
- Unit Price (auto-filled from Amount, can override)
- Tax Rate (defaults to 0%)

### Step 3: Review and Edit Information

#### Auto-filled Fields
These fields are automatically populated from your form:
- **Vendor Name** ← from Store/Vendor Name field
- **Student Name** ← from Student selection
- **Invoice Number** ← from PO Number (format: YYYYMMDD_HHMM)
- **Invoice Date** ← today's date
- **Description** ← from Comment field
- **Unit Price** ← from Amount field

#### Customizing Fields

You can edit any invoice field directly:
- **Description:** Change from comment to custom description
- **Quantity:** For multiple units (defaults to 1)
- **Unit Price:** Override if different from total amount
- **Tax Rate:** Add sales tax if applicable (as percentage, e.g., 8.25)

### Step 4: Edit Vendor Information (Optional)

Click the **"Edit"** button next to Vendor Name to open the Vendor Edit modal.

**You can:**
- Update vendor name and business name
- Change address, phone, email
- Set default tax rate for this vendor

**Save Options:**
1. **Save Profile (Permanent)** - Saves changes to vendor database
   - Changes apply to all future invoices for this vendor
   - Useful for updated contact info, address changes
   - Blue "Save Profile" button

2. **Apply (This Invoice)** - Uses changes only for this invoice
   - Temporary changes that don't affect future invoices
   - Primary button "Apply"

### Step 5: Edit Student Information (Optional)

Click the **"Edit"** button next to Student Name to open the Student Edit modal.

**You can:**
- Update student name
- Change address lines

**Save Options:**
1. **Save Profile (Permanent)** - Saves to student database
2. **Apply (This Invoice)** - Temporary changes

### Step 6: Generate Invoice

Click the **"Generate Invoice"** button.

**What happens:**
1. Status message shows "Generating invoice..."
2. System generates two files:
   - Excel file (.xlsx) - editable spreadsheet
   - PDF file (.pdf) - for submission
3. Files are saved to: `/path/to/esa/student_b/2025/` (student-specific folder)
4. Success message displays with file locations

**Example output paths:**
- Excel: `/path/to/esa/student_b/2025/20251103_1230.xlsx`
- PDF: `/path/to/esa/student_b/2025/20251103_1230.pdf`

### Step 7: Review Invoice Preview

A modal appears showing:
- Invoice summary (all details)
- Calculated subtotal, tax, and total
- File paths for both Excel and PDF versions

**Next Steps:**
- Click **"Continue to File Upload"** to proceed with submission
- The generated PDF is automatically added to your Invoice files
- You can still upload additional documents (Receipt, Attestation, etc.)

## Vendor Profiles

### What are Vendor Profiles?

Vendor profiles store recurring vendor information:
- Business name
- Address
- Phone and email
- Default tax rate

**Pre-loaded Vendors:**
- Instructor (AZ Ice)

### Adding a New Vendor Profile

1. In Edit Vendor modal, fill in all information
2. Click **"Save Profile (Permanent)"**
3. Profile is saved to database
4. Automatically available for future invoices

### When to Update Vendor Profiles

Update a profile when:
- Vendor address changes
- Phone/email is incorrect
- Tax rate needs updating
- Business name changes

### Temporary vs. Permanent Changes

| Action | Scope | Use Case |
|--------|-------|----------|
| **Apply (This Invoice)** | Current invoice only | One-time address change |
| **Save Profile (Permanent)** | All future invoices | Updated contact info |

## Student Profiles

Similar to vendor profiles, student profiles store:
- Student name
- Address line 1
- Address line 2 (City, State ZIP)

**Pre-loaded Students:**
- Student A
- Student B
- Student C

### When to Update Student Profiles

Update when:
- Student address changes
- Name spelling correction needed

## Customizing Invoices

### Invoice Fields You Can Change

All invoice fields can be customized before generation:

| Field | Default | Editable | Example |
|-------|---------|----------|---------|
| Invoice Number | From PO# | Yes | 20251103_1230 |
| Date | Today | Yes | 11/3/2025 |
| Description | From comment | Yes | Ice skating lesson |
| Quantity | 1 | Yes | 1, 2, 3... |
| Unit Price | From amount | Yes | 45.00, 50.00 |
| Tax Rate | 0% | Yes | 0, 8.25, 10 |

### Example: Multiple Units

If paying for 3 hours of tutoring at $50/hour:
- Unit Price: 50.00
- Quantity: 3
- Result: $150.00 subtotal

### Example: With Sales Tax

If vendor charges 8.25% sales tax:
- Unit Price: 45.00
- Quantity: 1
- Tax Rate: 8.25
- Result: $45.00 + $3.71 tax = $48.71 total

## File Organization

Generated invoice files are saved to:

```
/path/to/esa/documents/
├── student_b/
│   ├── 2024/
│   └── 2025/
│       ├── 20251103_1230.xlsx    (Excel - editable)
│       ├── 20251103_1230.pdf     (PDF - for submission)
│       ├── receipt_payment.pdf
│       ├── attestation.pdf
│       └── ...
├── student_a/
│   ├── 2024/
│   └── 2025/
│       └── ...
└── student_c/
    ├── 2024/
    └── 2025/
        └── ...
```

**Organization:**
- By student (student_a, student_b, student_c)
- By year (2024, 2025, etc.)
- Named by invoice number (YYYYMMDD_HHMM)

## Editing Generated Invoices

### Editing the Excel File

The generated Excel file is fully editable:

1. Locate the file in student folder
2. Open in Excel (or Numbers on Mac)
3. Make changes (vendor info, amounts, etc.)
4. Save the file
5. Use the Excel file OR convert to PDF again

**Important:** If you edit the Excel file, the PDF won't auto-update. You'll need to:
- Save your changes in Excel
- Export as PDF manually (File → Export as PDF)
- Or keep the generated PDF and note the changes

### Editing the PDF

PDFs are not easily editable. If you need to make changes:
1. Edit the Excel file instead
2. Export to PDF again
3. Or use an online PDF editor (not recommended for sensitive financial data)

## Troubleshooting

### Issue: "Vendor not found"

**What it means:** The vendor name doesn't match a saved profile.

**Solution:**
- Edit vendor info in modal
- Click "Save Profile" to create new profile
- Or just use temporary edit ("Apply")

### Issue: Invoice generation fails

**Possible causes:**
1. Missing required field (invoice number, date, etc.)
   - Solution: Fill in all fields

2. Invalid path or permissions
   - Check that student folder exists
   - Verify write permissions

3. LibreOffice not installed (PDF won't generate)
   - Excel file still created
   - Solution: Install LibreOffice via `brew install libreoffice`

### Issue: PDF not generated, only Excel

**Causes:**
- LibreOffice not installed on system
- LibreOffice conversion failed

**Solution:**
- Excel file is still usable
- Install LibreOffice: `brew install libreoffice`
- Or manually convert Excel to PDF in Excel/Numbers

### Issue: Wrong vendor/student selected

**If you notice before generating:**
- Edit the fields in the modal
- Click "Apply (This Invoice)"
- Generate again

**If you notice after generating:**
- Delete the generated files
- Edit the form
- Generate again

## Best Practices

### Naming Convention

Keep invoice numbers consistent:
- Format: `YYYYMMDD_HHMM` (e.g., 20251103_1430)
- Matches PO Number format
- Easy to organize and track

### Profile Management

**Keep profiles up to date:**
- Update when vendor info changes
- Remove outdated information
- Saves time on future invoices

**Avoid duplicate profiles:**
- Don't create multiple profiles for the same vendor (e.g., "Instructor A" and "Instructor A (2025)")
- Keep one canonical profile per vendor
- Edit existing profiles instead of creating new ones

### Description Clarity

Write clear descriptions for invoices:
- ✅ "Ice skating lesson - 11/3/2025"
- ✅ "Tutoring session (1 hour)"
- ✅ "Curriculum materials - Math"
- ❌ "lesson"
- ❌ "stuff"

### Quantity and Unit Price

Think about how to structure amounts:
- For single items: Qty=1, Price=$45.00
- For multiple units: Qty=3, Price=$50.00 (for 3 hours)
- For bulk: Qty=2, Price=$25.00 (for 2 books)

## FAQ

### Q: Is invoice generation required?

**A:** No! It's completely optional. You can:
- Skip invoice generation and upload existing file
- Check the "Generate invoice" checkbox anytime
- Generate multiple invoices (one per submission)

### Q: Can I use an existing invoice instead?

**A:** Yes! You can:
1. Skip the "Generate invoice" checkbox
2. Use file browser to select your existing invoice
3. Proceed normally with submission

### Q: What if I use the same vendor multiple times?

**A:** The system remembers vendor profiles. After first use:
1. Select student, amount, etc.
2. Check "Generate invoice"
3. Vendor info auto-populates
4. Just edit date/amount and generate

### Q: Can I save a draft and come back later?

**A:** Currently, no. But you can:
1. Take a screenshot of the form
2. Note any custom invoice settings
3. Come back and re-enter the information
4. Or modify the generated Excel file manually

### Q: Does LibreOffice need to stay open?

**A:** No! LibreOffice runs in background ("headless" mode) and doesn't need to be visible. The PDF generates automatically.

### Q: Can I change tax rate per invoice?

**A:** Yes! The Tax Rate field can be set for each invoice independently. You can also set a default tax rate in the vendor profile, which can be overridden per invoice.

### Q: What format is the PDF?

**A:** The PDF is generated directly from your Excel template using LibreOffice. It has:
- Professional formatting matching your template
- All calculations included
- Ready to submit to ClassWallet

## Support

For issues or questions:
1. Check INVOICE_FEATURE.md for technical details
2. Check this guide's Troubleshooting section
3. Review terminal logs for error messages
4. Check if LibreOffice is installed (`which libreoffice`)

## Summary

The invoice generation feature:
- ✅ Saves 5-10 minutes per submission
- ✅ Reduces manual Excel work
- ✅ Maintains vendor/student profiles
- ✅ Optional - you can skip if not needed
- ✅ Fully editable files (Excel)
- ✅ Professional PDF output
- ✅ Organized file storage by student/year

Next time you have a lesson or activity charge, check "Generate invoice" and let the automation do the work!
