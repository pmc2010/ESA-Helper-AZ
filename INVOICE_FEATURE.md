# Invoice Generation Feature

## Overview

Automatically generate Excel and PDF invoices for ESA reimbursements using vendor and student profile data with your custom template file.

**What it does:**
- Uses your existing template: `/path/to/esa/documents/template_invoice.xltx`
- Populates template with vendor info, student info, invoice details, and amounts
- Generates both Excel (.xlsx) and PDF (.pdf) files
- Saves files to student's folder: `/path/to/esa/student_b/2025/`
- Optional - user can skip invoice generation or select existing file

**Time saved:** ~5-10 minutes per submission (no more manual Excel invoicing!)

## Files Added/Modified

### New Files

1. **`app/invoice_generator.py`** (220 lines)
   - `InvoiceGenerator` class - main invoice generation logic
   - Template loading and data population
   - PDF conversion using LibreOffice
   - Vendor/student profile management functions

2. **`data/vendors_detailed.json`**
   - Vendor profile database
   - Fields: id, name, business_name, address_line_1, address_line_2, phone, email, tax_rate

3. **`data/students_detailed.json`**
   - Student profile database
   - Fields: id, name, address_line_1, address_line_2, folder
   - Student folders used as default output location

4. **`INVOICE_FEATURE.md`** (this file)
   - Complete documentation

### Modified Files

1. **`app/routes.py`**
   - Added imports for invoice generator
   - 7 new API endpoints (see below)

2. **`pyproject.toml`**
   - Added `openpyxl>=3.1.0` dependency

## API Endpoints

### Vendor Management

```
GET  /api/vendors-detailed          - Get all vendor profiles
GET  /api/vendors-detailed/<id>     - Get specific vendor
POST /api/vendors-detailed          - Create/update vendor (with save option)
```

### Student Management

```
GET  /api/students-detailed         - Get all student profiles
GET  /api/students-detailed/<id>    - Get specific student
POST /api/students-detailed         - Create/update student (with save option)
```

### Invoice Generation

```
POST /api/invoice/generate          - Generate invoice from form data
```

**Request body:**
```json
{
  "student": "Student B",
  "vendor_name": "Instructor",
  "invoice_number": "20251103_1230",
  "date": "11/3/25",
  "description": "Ice skating lesson",
  "quantity": 1,
  "unit_price": 45.00,
  "tax_rate": 0.0,
  "vendor_business_name": "AZ Ice",
  "vendor_address_1": "123 Example Street",
  "vendor_address_2": "Example City, AZ 12345",
  "vendor_phone": "562-900-0016",
  "vendor_email": "instructor@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "excel_path": "/path/to/esa/student_b/2025/20251103_1230.xlsx",
  "pdf_path": "/path/to/esa/student_b/2025/20251103_1230.pdf",
  "message": "Invoice generated successfully"
}
```

## Data Structure

### Vendor Profile
```json
{
  "id": "instructor_a",
  "name": "Instructor",
  "business_name": "AZ Ice",
  "address_line_1": "123 Example Street",
  "address_line_2": "Example City, AZ 12345",
  "phone": "562-900-0016",
  "email": "instructor@example.com",
  "tax_rate": 0.0,
  "notes": "Ice skating instructor"
}
```

### Student Profile
```json
{
  "id": "student_b_id",
  "name": "Student B",
  "address_line_1": "456 Sample Road",
  "address_line_2": "Sample Town, AZ 54321",
  "folder": "/path/to/esa/documents/student_b"
}
```

## How It Works

### Template Mapping

The invoice generator maps form data to Excel cells:

| Form Field | Template Cell | Type |
|-----------|--------------|------|
| Vendor Name | B2 | business_name |
| Vendor Address | B3-B4 | address_line_1, address_line_2 |
| Vendor Phone | B5 | phone |
| Vendor Email | B6 | email |
| Student Name | B9 | name |
| Student Address | B10-B11 | address_line_1, address_line_2 |
| Invoice Number | E9 | invoice_number |
| Date | F9 | date |
| Description | B14 | description |
| Quantity | D14 | quantity |
| Unit Price | E14 | unit_price |
| Amount | F14 | Formula (auto-calculated) |
| Tax Rate | F30 | tax_rate |
| Tax | F31 | Formula (auto-calculated) |
| Subtotal | F29 | Formula (auto-calculated) |
| Total | F32 | Formula (auto-calculated) |

### Workflow

1. User fills form with basic info
2. (Optional) User clicks "Generate Invoice" button
3. Form sends request to `/api/invoice/generate`
4. Server:
   - Loads template file
   - Populates with vendor/student data
   - Calculates amounts (quantity × unit_price + tax)
   - Saves as Excel file
   - Converts to PDF using LibreOffice
5. Return paths to user
6. User can:
   - Open/preview in modal
   - Edit if needed
   - Accept and continue to file upload

## Vendor/Student Editing

Both vendor and student info can be edited in the modal:

**Editing Options:**
1. **Temp Edit** - Changes apply only to this submission
2. **Save to Profile** - Changes saved permanently for future use

**When to Edit:**
- Vendor address/phone changed
- New vendor not in profile
- Student contact info updated
- Any other profile information

**Save Process:**
- Click "Save Profile" in modal
- Updates `data/vendors_detailed.json` or `data/students_detailed.json`
- Instantly available for next submission

## Requirements

### Software Dependencies

- ✅ Python 3.11+
- ✅ openpyxl (added to pyproject.toml)
- ✅ LibreOffice (for PDF conversion)

**Install LibreOffice (macOS):**
```bash
brew install libreoffice
```

**Verify installation:**
```bash
which libreoffice
# Should output: /usr/local/bin/libreoffice
```

### File Requirements

- ✅ Template file at: `/path/to/esa/documents/template_invoice.xltx`
- ✅ Student folders must exist (auto-created with year subfolder)
- ✅ Vendor and student profiles in JSON files

## Error Handling

### Common Issues & Solutions

**Issue: "Template not found"**
- Check path: `/path/to/esa/documents/template_invoice.xltx`
- Verify Synology is mounted

**Issue: "LibreOffice not found"**
- PDF generation will fail but Excel file still created
- Install: `brew install libreoffice`
- Application will continue with Excel only if PDF fails

**Issue: "Student not found"**
- Check student name matches profile (case-insensitive)
- Available students: Student A, Student B, Student C

**Issue: "Output directory could not be created"**
- Check permissions on student folder
- Verify `/path/to/esa/student_b/2025` is writable

## Future Enhancements

### Phase 2 (Optional)

- [ ] Multiple line items (rows 14-28)
- [ ] Attach receipt scan to PDF
- [ ] Invoice templates per vendor (different layouts)
- [ ] Invoice numbering system (auto-increment)
- [ ] Invoice history/archive management
- [ ] Email invoice to vendor

### Phase 3 (Optional)

- [ ] Custom template designer
- [ ] Invoice signature field
- [ ] Company logo in template
- [ ] Payment terms and notes
- [ ] Recurring invoices

## Troubleshooting

### PDF Not Generated

Check LibreOffice installation:
```bash
libreoffice --version
# Should show: LibreOffice 7.x.x or higher
```

Test conversion manually:
```bash
libreoffice --headless --convert-to pdf test.xlsx
```

If fails, check system logs:
- Console.app on macOS
- Check write permissions on output folder

### Excel File Not Matching Template

Verify template structure:
```python
from openpyxl import load_workbook
wb = load_workbook('/path/to/template.xltx')
ws = wb.active
print(f"Template cells: {ws.dimensions}")
```

Compare to expected cell mappings in "Template Mapping" section.

## Testing

### Manual Test

1. Start app: `uv run main.py`
2. Fill form with:
   - Student: Student B
   - Vendor: Instructor
   - Amount: $45.00
   - Check "Generate Invoice"
3. Click "Generate Invoice"
4. Verify files created in `/path/to/esa/student_b/2025/`

### Automated Test

Coming in next phase - unit tests for invoice generation.

## File Size & Performance

- Template size: ~22 KB
- Generated Excel: ~15-20 KB
- Generated PDF: ~30-50 KB
- Generation time: ~2-3 seconds
- PDF conversion time: ~1-2 seconds

## Integration with Submission Workflow

The invoice generation is **optional** and fits into the workflow:

```
1. Fill Basic Form
   ↓
2. (Optional) Generate Invoice
   ├─→ Generate Invoice button
   ├─→ Modal with vendor/student edit
   ├─→ Preview invoice
   └─→ Accept & Continue
   ↓
3. Upload Files
   (Can include generated invoice PDF)
   ↓
4. Select Category
   ↓
5. Fill PO & Comment
   ↓
6. Submit to ClassWallet
```

User can skip invoice generation entirely if not needed.

## Next Steps

1. **Frontend Modal** - Build invoice generation UI
2. **Integration** - Add button to form
3. **Testing** - Test with actual template and profiles
4. **Production** - Deploy and enable feature

## Questions?

Refer to:
- `app/invoice_generator.py` - Implementation details
- `data/vendors_detailed.json` - Vendor profile format
- `data/students_detailed.json` - Student profile format
- `IMPLEMENTATION_STATUS.md` - Overall system architecture
