# Arizona ESA Reimbursement Workflow

## Overview
This document outlines the current manual process for submitting ESA (Education Savings Account) reimbursements through ClassWallet for homeschooled children in Arizona.

## Background Context
- **Program**: Arizona ESA (Education Savings Account)
- **Fund Manager**: ClassWallet
- **Purpose**: State funds for educational purposes for homeschooled children
- **Interaction Methods**:
  1. Submit reimbursement for items/activities paid with personal money
  2. Use direct pay option with pre-approved vendors

## Current Workflow Example: Ice Skating Lessons

### Step 1: Payment & Photo Capture
1. Pay instructor through Venmo
2. Receive payment confirmation in Venmo (with timestamp/amount)
3. Take screenshots of Venmo payments from phone

### Step 2: Transfer Images to Laptop
1. Screenshots sent to self via text message
2. Images automatically synced from phone to Synology Photos
3. Images accessible from Synology drive on laptop
4. Alternative: Take screenshots of screenshots from text messages on laptop (if needed for clarity)

### Step 3: Documentation Preparation

#### Payment Evidence PDF
1. Open Word document template
2. Paste Venmo payment screenshots (typically 2 images showing payment details)
3. Save as PDF

#### Invoice PDF
1. Create invoice in Excel with:
   - Lesson details
   - Instructor name
   - Amount paid
   - Date of lesson
2. Save as PDF

#### Attestation Form
- Instructor attestation form (prepare separately)
- Keep in PDF format

### Step 4: ClassWallet Reimbursement Submission

#### Navigation & Initial Setup
1. Log into ClassWallet
2. Select child's account
3. Click "Start a new Reimbursement" button

#### Step 1: Basic Information
1. **Store Name**: Enter instructor's name
2. **Payment Amount**: Enter lesson amount
3. Click **Next**

#### Step 2: Document Upload
1. Upload 3 documents:
   - Payment proof PDF (Venmo screenshots)
   - Invoice PDF
   - Instructor attestation form
2. Click **Next**

#### Step 3: Category Selection
1. Check box: **Arizona - ESA**
2. **Expense Category**: Select "Tutoring and teaching services - Accredited Individual"
3. Click **Next**

#### Step 4: Purchase Order & Notes
1. **Purchase Order Number**: Format as `YYYYMMDD_hhmm` (e.g., `20231215_1430`)
   - Use current date and time of submission
2. **Comment**: Format as `AZ [Activity] - YYYY-MM-DD` (e.g., `AZ Ice lesson - 2023-12-15`)
3. Click **Next**

#### Step 5: Complete
1. Review submission
2. Click **Close**

## Time Investment
- This entire process is currently time-consuming, spanning multiple applications and devices
- Typical workflow involves:
  - Screenshot capture and transfer (~5-10 minutes)
  - Word document creation and PDF export (~5 minutes)
  - Excel invoice creation and PDF export (~5-10 minutes)
  - ClassWallet form submission (~5-10 minutes)
  - **Total: Approximately 20-40 minutes per lesson reimbursement**

## Key Pain Points
1. Manual multi-step image transfer process
2. Repeated document creation across multiple applications
3. Need to manually create PO numbers and format comments
4. Multiple copy-paste operations required
5. Prone to formatting errors or missed steps

## Potential Automation Opportunities
- Automated screenshot collection and organization
- Template-based PDF generation
- ClassWallet API integration (if available)
- Batch processing for multiple lessons
- Automated PO number generation
- Form pre-filling and auto-submission

## File Locations & Systems
- **Phone**: Screenshots, Venmo app
- **Synology Drive**: Image backup and access
- **Laptop**: Word templates, Excel templates, ClassWallet web interface
- **ClassWallet**: Web-based reimbursement system (login required)

---

# ESA Helper Tool - Automated Solution Requirements

## Project Overview
Build an automated web-based tool (Flask + Bootstrap) to streamline ESA reimbursement and direct pay submissions through ClassWallet. The tool will provide a form-based interface with template system, image management, and full ClassWallet automation.

## User Profile
- **Students**: 3 children (Student A, Student B, Student C)
- **Usage Frequency**: New templates approximately once per month
- **Primary Goal**: Reduce 20-40 minute manual process to < 5 minutes

## Core Features

### 1. Student Management
- **3 Students**: Student A, Student B, Student C
- **Student-Specific Paths**: Each student has a base Synology path structure:
  - Student A: `/path/to/esa/documents/student_a/<current_year>`
  - Student B: `/path/to/esa/documents/student_b/<current_year>`
  - Student C: `/path/to/esa/documents/student_c/<current_year>`
- **Students can have different vendors/templates** (e.g., Student A does ice skating, Student B does piano, etc.)

### 2. Template System

#### Template Fields
Templates pre-fill the following fields:
- Student name
- Store Name / Vendor name
- Request Type (Reimbursement or Direct Pay)
- Expense Category
- Any other context-specific information

#### Template Storage
- Stored as JSON or YAML files in a `templates/` directory
- Example template name: `Lesson_Template_A.json`
- Each template includes:
  - Student name
  - Store/Vendor name
  - Request type
  - Expense category
  - Payment amount (optional, for quick reference)

#### Template Usage
- User selects template from dropdown → form auto-populates but remains **fully editable**
- New templates created approximately once per month via UI

### 3. Form Interface

#### Form Fields
```
Student: [Dropdown - Student A, Student B, Student C]
Template: [Dropdown - loads available templates, auto-populates form]
Request Type: [Dropdown - Reimbursement / Direct Pay]
Store Name: [Text input]
Amount: [Currency input, auto-calculated if possible, editable]
Expense Category: [Dropdown - see expense categories below]
[Image Upload Fields - Dynamic based on expense category]
PO Number: [Auto-generated as YYYYMMDD_hhmm, editable]
Comment: [Text input, suggested format: "AZ [Activity] - YYYY-MM-DD"]
```

#### Dynamic Image Upload Fields
Based on selected **Expense Category**, show required upload fields:

1. **Computer Hardware & Technological Devices**
   - Receipt (showing student name, purchase amount, item purchased, funding source)

2. **Curriculum**
   - Receipt (showing student name, purchase amount, item purchased, funding source)

3. **Tutoring & Teaching Services – Accredited Facility/Business**
   - Receipt (showing student name, purchase amount, item purchased, funding source)
   - Invoice (showing student name, purchase amount, item to be purchased)

4. **Tutoring & Teaching Services – Accredited Individual**
   - Receipt (showing student name, purchase amount, item purchased, funding source)
   - Invoice (showing student name, purchase amount, item to be purchased)
   - Attestation Form (instructor attestation)

5. **Supplemental Materials (Curriculum Always Required)**
   - Curriculum (showing item/activity as required material/supply)
   - Receipt (showing student name, purchase amount, item purchased, funding source)

#### Image Management Features
- **File Browser**: Browse files from mounted Synology drive
- **Image Preview**: Display preview of selected images before submission
- **Image Annotation** (Nice-to-have): Add student name and highlight relevant purchases on receipts
- **Recent Folders**: Remember last 5 folders used for faster browsing
- **Student-Specific Base Path**: Auto-navigate to student's folder for faster access

### 4. Form Validation & Safety
- ✅ Validate all required files are selected based on expense category
- ✅ Show confirmation dialog before ClassWallet submission showing:
  - All form fields
  - All selected images (preview)
  - Final PO number and comment
  - Request type (Reimbursement or Direct Pay)
- ✅ Allow cancellation at confirmation step

### 5. ClassWallet Automation

#### Child Selection
- One parent login (stored in config)
- ClassWallet dropdown selector for 3 children: Student A, Student B, Student C
- Selected child is used throughout reimbursement/direct pay flow

#### Reimbursement Workflow
1. Auto-login with stored parent credentials
2. Use dropdown to select a student account (Student A, Student B, or Student C)
3. Click "Start a new Reimbursement" button
4. Fill basic info (Store Name, Amount)
5. Click Next
6. Upload all required images
7. Click Next
8. Select "Arizona - ESA" checkbox
9. Select expense category
10. Click Next
11. Auto-fill PO number
12. Auto-fill comment
13. Click Next
14. Click Close

#### Direct Pay Workflow
1. Auto-login with stored parent credentials
2. Use dropdown to select a student account (Student A, Student B, or Student C)
3. Click "Pay" button (Direct Pay section)
4. Search for vendor from pre-approved vendor list (exact name match) and click Pay button to select
5. Input payment amount
6. Click Next
7. Upload screenshots (receipt + category-specific docs, NO payment screenshot)
8. Select "Arizona - ESA" checkbox
9. Select expense category
10. Auto-fill comment and PO number
11. Click Next
12. Click Close

#### Key Differences: Direct Pay vs. Reimbursement
- **Reimbursement**: Requires payment receipt (Venmo screenshot, etc.)
- **Direct Pay**: Does NOT require payment receipt (vendor payment direct from account)
- Everything else is identical

### 6. Credential Management
- ✅ Store ClassWallet credentials locally in plain-text config (single user device)
- ✅ One parent login with dropdown selector for 3 children
- ✅ Auto-login on submission (user does not re-enter credentials each time)
- ✅ Credentials stored in `config.json` (local, plaintext)

### 7. Post-Submission Behavior
- ✅ Show success confirmation message
- ✅ **Keep form populated** (in case user needs to submit multiple related items)
- ✅ Add "Clear Form" button to reset all fields and start fresh
- ✅ Keep submission history/log (for user records)

---

## Technology Stack

### Backend
- **Framework**: Flask (lightweight, Python-based)
- **Automation**: Selenium (web browser automation for ClassWallet)
- **Credential Storage**: Plain-text JSON config file (`config.json`)

### Frontend
- **Framework**: Bootstrap 5
- **Images**: Local file browser with image preview
- **Form Handling**: HTML5 forms with client-side validation
- **Vendor List**: Pre-approved vendors stored in JSON (editable via admin UI)

### File System
- Synology drive mounted as `/Volumes/...`
- Templates stored as JSON in `templates/` directory
- Vendors stored as JSON in `vendors/` directory
- Config file stored as `config.json` (credentials)
- Submission logs stored in `logs/` directory

---

## User Experience Improvements

1. **Quick-Select Expense Categories**: Common categories (like "Tutoring & Teaching - Accredited Individual") appear at top
2. **PO Number Auto-Generation**: Generates `YYYYMMDD_hhmm` format, user can override
3. **Amount Auto-Calculation**: If invoice data available, suggest amount (editable)
4. **Recent Paths**: Remember last 5 image folder locations for faster browsing
5. **Template Creation Wizard**: Simple form to create new templates (runs ~once/month)
6. **Submission Confirmation**: Review all details before submitting
7. **Clear Button**: Reset form after submission if needed
8. **Submission History**: Log of what was submitted (timestamps, amounts, students)

---

## Security Considerations

1. **Credentials Storage**: Local encryption recommended (keyring library)
2. **File Access**: Only access mounted Synology drive paths
3. **Session Management**: Auto-logout after inactivity
4. **No Cloud Sync**: All data stays local
5. **Secure Form**: HTTPS for local server (development mode okay for localhost)

---

## Implementation Roadmap

### Phase 1: Core Web Form
- [ ] Flask app setup
- [ ] Form layout with Bootstrap
- [ ] Student dropdown
- [ ] Template system (load/select)
- [ ] Dynamic image upload based on expense category
- [ ] Image preview functionality

### Phase 2: Image Management & File Handling
- [ ] File browser for Synology paths
- [ ] Image preview
- [ ] Recent folders tracking
- [ ] Image annotation (nice-to-have)

### Phase 3: Automation & ClassWallet Integration
- [ ] Selenium-based ClassWallet automation
- [ ] Reimbursement workflow
- [ ] Direct Pay workflow
- [ ] Credential management

### Phase 4: Polish & Enhancements
- [ ] Confirmation dialog
- [ ] Submission logging
- [ ] Template creation wizard
- [ ] Error handling & user feedback
- [ ] Clear Form button behavior

---

## Next Steps
1. Finalize form layout and field requirements
2. Set up Flask project structure
3. Create template data structure and examples
4. Build form interface
5. Implement image handling
6. Build ClassWallet automation logic
