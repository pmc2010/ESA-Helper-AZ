# ESA Helper - Arizona Empowerment Scholarship Account (ESA) ClassWallet Automation

**Automate your Arizona ESA reimbursements and direct vendor payments in ClassWallet. Reduce submission time from 20-40 minutes to 5-25 minutes.**

ESA Helper is a comprehensive desktop application that automates Empowerment Scholarship Account (ESA) reimbursement submissions and direct vendor payments through ClassWallet. Perfect for Arizona families using ESA funds for tutoring, curriculum, and educational services. Includes tools for managing student profiles, vendor information, reusable submission templates, and invoice generation.

**Keywords**: Arizona ESA | Empowerment Scholarship Account | ClassWallet Automation | ESA Reimbursement | Arizona Educational | Direct Pay Automation

---

## ⚠️ Disclaimer & No Warranty

**IMPORTANT: Please read this carefully before using ESA Helper.**

### No Affiliation
This tool is **not affiliated with, endorsed by, or officially connected to:**
- ClassWallet (the payment platform)
- The State of Arizona
- The Arizona Department of Education
- The Arizona ESA program or any government agency

This is an **independent, third-party automation tool** created to help families manage their ESA submissions.

### No Guarantees or Warranties
**USE AT YOUR OWN RISK.** This software is provided "as-is" with:
- **No warranty** of any kind, express or implied
- **No guarantee** it will work with future versions of ClassWallet
- **No liability** for any loss, damage, or incorrect submissions
- **No support** beyond community help

### Your Responsibility
You are entirely responsible for:
- Verifying that all submissions are correct before they're processed
- Ensuring you comply with all Arizona ESA program rules and requirements
- Checking your ClassWallet account after submissions to confirm they worked
- Keeping your credentials and data secure
- Backing up your data regularly

### Important Notes
- **ClassWallet updates may break the tool** - If ClassWallet changes their interface, this tool may stop working until selectors are updated
- **Always verify submissions manually** - Don't assume the tool worked correctly; check ClassWallet to confirm
- **Test with small amounts first** - Use templates and test submissions before processing large amounts
- **Keep records** - Maintain your own records of all submissions independent of this tool

### What We've Done Right
The creator of this tool:
- **Uses it personally** with their own ESA account and family
- **Has tested thoroughly** across multiple submission types and scenarios
- **Made significant efforts** to ensure reliability and security
- **Maintains the code** and fixes issues as they're discovered
- **Shares the code openly** so you can audit it and understand what it does

### If Something Goes Wrong
If the tool fails to submit or submits incorrectly:
1. **Check ClassWallet immediately** - See what was actually submitted
2. **Correct any errors manually** - Don't rely on the tool to fix itself
3. **Report the issue** - Open a GitHub issue with details so it can be fixed
4. **Contact ClassWallet support** - They are the authority on account issues

---

## ✨ Features

### 🚀 Core Features

- **Automated ClassWallet Submissions** - Submit reimbursement requests and direct pay vendor payments with one click
- **Direct Pay Automation** - Automated vendor payment workflow with vendor search and category selection
- **Invoice Generation** - Create professional Excel and PDF invoices from templates with vendor and student data
- **Multi-Family Support** - Run on multiple computers with different ESA accounts and student data
- **Student/Vendor Management** - Easily manage student profiles and vendor information
- **Reimbursement Templates** - Create templates for recurring expenses (e.g., weekly lessons)
- **Smart File Handling** - Auto-load direct file paths or browse directories for attachments
- **Intelligent Automation** - Selenium-powered browser automation with fallback selectors
- **Submission History** - Track all submitted reimbursements and payments with complete details

### 📚 Additional Tools

- **Curriculum Generator** - Generate curriculum documents using ChatGPT templates
  - Create templates with dynamic placeholders
  - Auto-generate ChatGPT prompts
  - One-click copy-to-clipboard
  - Paste ChatGPT response and generate PDFs

- **Data Migration** - Export/import all your data for backup or transfer
  - Complete data backup to JSON
  - Import previously exported files
  - Share data with family members

- **Setup Wizard** - First-time configuration for non-technical users
  - ESA credentials setup
  - System requirements overview
  - OS-specific installation guide

## 🎯 Use Cases

**Perfect for Arizona families who use Empowerment Scholarship Accounts for:**

- 👩‍🏫 **Tutoring Services** - Automate reimbursements for tutors and tutoring centers
- 📚 **Curriculum Purchases** - Submit receipts for textbooks, workbooks, and educational materials
- 🖥️ **Technology & Software** - Track computer equipment and educational software expenses
- 🎨 **Enrichment Activities** - Manage payments for music lessons, sports, coding classes
- 📋 **Vendor Payments** - Direct vendor payments with automatic invoice generation
- 📊 **Batch Processing** - Handle multiple submissions efficiently with templates
- 📁 **Documentation** - Professional invoice generation and expense tracking

**Supports these Arizona ESA features:**
- ClassWallet Reimbursement requests (personal reimbursement)
- ClassWallet Direct Pay (vendor payments)
- Multiple expense categories
- Arizona ESA purse selection
- Receipt and invoice documentation

## Installation

### Quick Start

1. **Install Python 3.11+**
   - [Download Python](https://www.python.org/downloads/)
   - macOS: `brew install python@3.11`
   - Windows: Use official installer
   - Linux: `sudo apt-get install python3.11`

2. **Install uv (Python Package Manager)**
   - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - Or use Homebrew: `brew install uv`

3. **Install Google Chrome**
   - ESA Helper uses Selenium with Chrome for automation
   - [Download Chrome](https://www.google.com/chrome/) or `brew install --cask google-chrome`

4. **Install LibreOffice (Optional)**
   - Needed for Excel to PDF conversion
   - macOS: `brew install libreoffice`
   - Windows: [Download Installer](https://www.libreoffice.org/download/)
   - Linux: `sudo apt-get install libreoffice`

5. **Download and Run**
   ```bash
   git clone https://github.com/petermandy/ESA-Helper-AZ.git
   cd ESA-Helper-AZ
   uv run main.py
   ```
   The app will open automatically in your browser at `http://127.0.0.1:5000`

   **Note:** The default port is 5000. To use a different port, set the `PORT` environment variable:
   ```bash
   PORT=8080 uv run main.py
   ```
   Or edit `.env` file and change `PORT=5000` to your desired port.

## System Requirements

| Requirement | Details |
|---|---|
| **OS** | macOS, Windows, or Linux |
| **Python** | 3.11 or higher |
| **Browser** | Google Chrome (required for automation) |
| **LibreOffice** | Optional (for PDF conversion) |
| **Disk Space** | ~500MB (including dependencies) |
| **Internet** | Required for ClassWallet submission |

## Usage

### First-Time Setup

1. Run `uv run main.py`
2. App opens to setup page automatically
3. Enter your ESA ClassWallet credentials
4. (Optional) Add student profiles and vendors
5. Click "Save & Continue"

### Submitting a Reimbursement

1. **Select Student** - Choose which child the expense is for
2. **Choose Request Type** - Select "Reimbursement"
3. **Choose Template** (optional) - Use a saved template to auto-fill
4. **Enter Details** - Store name, amount, expense category, comment
5. **Upload Files** - Add receipts, invoices, and attestations
6. **Request Invoice** (optional) - Generate invoice from template
7. **Review & Submit** - See summary and submit via ClassWallet

### Submitting a Direct Pay Payment

1. **Select Student** - Choose which child the payment is for
2. **Choose Request Type** - Select "Direct Pay"
3. **Select Vendor** - Choose the vendor to pay (payment is sent directly to them)
4. **Enter Amount** - Specify the payment amount
5. **Select Category** - Choose the ESA expense category
6. **Choose Account** - Select which ESA purse to charge (e.g., "Arizona - ESA")
7. **Add Details** (optional) - Add comments and invoice/quote number
8. **Review & Submit** - Review details and submit via ClassWallet

**Note**: Direct Pay requires vendors to be configured with their ClassWallet search term for automatic lookup.

### Creating Reimbursement Templates

1. Go to Settings → Manage Templates
2. Select a student
3. Fill in template details (store name, amount, category, etc.)
4. Add file paths (direct files auto-load, directories allow browsing)
5. Save template

### Generating Curricula with ChatGPT

1. Go to Help → Curriculum Generator
2. Select student and create template with placeholders:
   ```
   Create a {CURRICULUM_TYPE} curriculum for a {AGE} year old
   girl named [STUDENT_NAME] with student ID [STUDENT_ID]
   that requires: {MATERIALS_LIST}
   ```
3. Fill in field values in the form
4. Review generated prompt and copy to clipboard
5. Paste in ChatGPT and get response
6. Paste response back to generate PDF

### Backing Up Your Data

1. Go to Help → Data Backup & Migration
2. Click "Download Backup File" to export all data
3. Store safely for recovery or sharing with family

## Project Structure

```
ESA-Helper-AZ/
├── app/
│   ├── __init__.py                 # Flask app setup
│   ├── routes.py                   # All API routes
│   ├── utils.py                    # Utility functions
│   ├── invoice_generator.py        # Excel/PDF invoice generation
│   ├── classwallet.py              # Selenium automation
│   ├── automation.py               # Main orchestration
│   ├── static/
│   │   ├── css/style.css           # Custom styles
│   │   └── js/app.js               # Frontend JavaScript
│   └── templates/
│       ├── index.html              # Main form
│       ├── setup.html              # First-time setup
│       ├── requirements.html       # Installation guide
│       ├── manage-students.html    # Student management
│       ├── manage-vendors.html     # Vendor management
│       ├── manage-templates.html   # Template management
│       ├── data-migration.html     # Backup/restore
│       └── curriculum-generator.html # Curriculum tool
├── data/
│   ├── students_detailed.json      # Student profiles
│   ├── vendors_detailed.json       # Vendor profiles
│   └── templates/
│       ├── student_b.json
│       ├── taylor.json
│       └── evie.json
├── main.py                         # Entry point
├── pyproject.toml                  # Python dependencies
└── README.md                        # This file
```

## Configuration Files

### config.json
```json
{
  "email": "your.email@example.com",
  "password": "your_classwallet_password",
  "students": {
    "Student A": "student_a_id",
    "Student B": "student_b_id",
    "Student C": "student_c_id"
  }
}
```
**Note**: Keep this file private! Never share it. It contains your ClassWallet credentials.

## FAQ

### Q: Does this work with Arizona Empowerment Scholarship Accounts?
A: Yes! ESA Helper is specifically designed for Arizona ESA families using ClassWallet. It automates both reimbursement requests and direct vendor payments (Direct Pay) through ClassWallet.

### Q: What expense categories are supported?
A: All Arizona ESA expense categories including: tutoring services, curriculum, computer hardware, supplemental materials, enrichment activities, and more. The app dynamically adapts to available categories in your ClassWallet account.

### Q: Can I use this for tutoring reimbursements?
A: Yes! ESA Helper is perfect for tutoring reimbursements. It automates the entire process from file upload to submission, and can create templates for recurring tutoring expenses.

### Q: How much time does this save?
A: Most families reduce submission time from 20-40 minutes to 5-25 minutes per submission. With templates for recurring expenses, you can save 70%+ of time.

### Q: Is my ClassWallet password stored securely?
A: Your ClassWallet credentials are stored locally in `config.json` on your computer. They are never sent to external servers. However, treat this file like a password - keep it private and don't share it.

### Q: Can I use this for multiple children/families?
A: Yes! Download the app on multiple computers and configure each with different ESA credentials. You can also export data from one installation and import on another.

### Q: Does this work with Direct Pay (vendor payments)?
A: Yes! Full Direct Pay automation is supported. Configure vendors with their ClassWallet search terms for automatic vendor lookup and payment processing.

### Q: What if LibreOffice isn't installed?
A: PDF generation will be skipped, but the Excel invoice will still be created. You can convert to PDF manually using Excel or another tool.

### Q: How do I backup my ESA data?
A: Go to Help → Data Backup & Migration and click "Download Backup File". Store it safely or share with family members.

### Q: Can I create templates for recurring expenses?
A: Yes! Go to Settings → Manage Templates. You can create templates for common expenses like weekly lessons, monthly subscriptions, or regular curriculum purchases.

### Q: Does this work on Mac/Windows/Linux?
A: Yes! It works on all major operating systems. Just make sure Python, Chrome, and uv are installed.

## Troubleshooting

### "LibreOffice not found"
- Install LibreOffice: `brew install libreoffice`
- Or download from [libreoffice.org](https://www.libreoffice.org/download/)
- PDF conversion will be skipped if not installed (Excel still works)

### "Chrome not found"
- Install Chrome: `brew install --cask google-chrome`
- Or download from [google.com/chrome](https://www.google.com/chrome/)
- ESA Helper looks for Chrome in standard locations

### "Port 5000 already in use"
- Another app is using port 5000
- Use a different port via the `PORT` environment variable:
  ```bash
  PORT=8080 uv run main.py
  ```
- Or edit the `.env` file and change `PORT=5000` to your desired port (e.g., `PORT=8080`)

### "Module not found" error
- Make sure you're using `uv run` not `python`
- `uv run` automatically installs dependencies

### Browser closes after submission
- This is intentional - app doesn't keep browser window open to save resources
- Check submission in ClassWallet manually if needed

## Performance Tips

1. **Create templates for recurring expenses** - Save 5+ minutes per submission
2. **Use direct file paths** - Auto-loaded files save time on file selection
3. **Batch similar submissions** - Process similar requests together
4. **Keep CSV of expenses** - Track what you've submitted

## Known Limitations & Important Notes

### ClassWallet Automation Limitations

1. **HTML selectors are brittle** - If ClassWallet updates their interface, selectors may break
2. **Multiple selector fallbacks** - The app tries 8 different selector combinations to find form elements
3. **Network dependent** - Requires stable internet connection during submission
4. **Browser integration** - Uses Selenium WebDriver; some ClassWallet features may require manual interaction

### File Organization Requirements

- Your document files must be accessible on your local filesystem
- Network drives (Synology, Google Drive, etc.) must be mounted as local folders
- Relative paths not supported - use absolute paths

### Data File Locations

This app stores all data locally on your computer:
- Student/vendor profiles: `data/students.json`, `data/vendors.json`
- Templates: `data/esa_templates/` directory
- Credentials: `config.json` in project root

**Keep backups** of important data in `data/` directory!

### Browser Automation Notes

- Requires Google Chrome/Chromium browser
- Browser window opens and closes during submission
- Cannot run multiple submissions simultaneously
- AutoFill and saved passwords may interfere with automation

### Known Issues

1. **Image editor popup during file upload** - App detects this popup and automatically clicks Save (implemented Nov 2025)
2. **Category selection requires multiple attempts** - Some forms may take 2-3 clicks to register selection
3. **LibreOffice PDF conversion** - May fail silently if LibreOffice not installed (but Excel still works)
4. **Special characters in file paths** - May cause issues with file browsing

## Development

### Adding New Features

1. **Backend Routes** → `app/routes.py`
2. **Frontend UI** → `app/templates/`
3. **Styles** → `app/static/css/style.css`
4. **JavaScript** → `app/static/js/app.js`

## Contributing

We welcome contributions! Areas that could use help:

- PDF generation from ChatGPT responses
- Recurring invoice templates
- Email invoice to vendor
- Multi-language support
- Dark mode
- Mobile app version

## Future Enhancements

- Direct ChatGPT API integration
- Automatic expense categorization with ML
- Receipt OCR for amount extraction
- Integration with other ESA platforms
- Cloud backup (optional)
- Scheduled submissions
- Invoice history and reporting
- Custom invoice templates

## Security & Privacy

### What We Do Right
- **Local Storage Only** - All data stored on your computer
- **No Cloud Uploads** - No data ever sent to external servers
- **No Tracking** - No analytics or telemetry
- **Open Source** - Code is transparent and auditable
- **Credentials Protected** - Passwords stored locally, not shared (not sent to external services)

### Important Security Notes

**This is an automation tool for personal family use.** While we take security seriously, please be aware:

1. **Credentials stored in plaintext** - ClassWallet email/password stored in `config.json` (protected by file permissions only)
2. **No encryption** - User data not encrypted at rest
3. **No authentication** - Web interface has no login (assumes only you access it)
4. **Limited input validation** - Some inputs not fully validated for format/content
5. **File access unrestricted** - Can access any file on your system that you have permission to read

### Security Best Practices

- Run on a **trusted computer only** (your personal device, not shared devices)
- Change your ClassWallet password regularly
- Keep credentials out of version control (they're in `.gitignore`)
- Don't share the code folder with others (contains your data)
- Use file permissions to restrict access to the project folder
- Enable your computer's screen lock when away

### If You Share This Tool

If sharing with other families:
1. Each person should use their own project folder (clone separately)
2. Each person configures their own credentials
3. Do not share the `data/` folder or `config.json`
4. Sample data provided in `*.sample.json` files - use these as templates

## License

MIT License - Feel free to modify and distribute

## Support

- **Questions?** Check the in-app Help menu
- **Bug Report?** Open an issue on GitHub
- **Feature Request?** Submit an issue with details

## Version History

### v2.0.0 (Current - November 2025)
- Multi-family support with setup wizard
- Student, vendor, template management
- Data backup and migration
- Curriculum generator with ChatGPT integration
- Comprehensive documentation
- Excel file corruption fix with template structure preservation
- Template file clearing on switching
- Auto-load direct file paths

### v1.0.0
- Basic ClassWallet automation
- Invoice generation
- Template system

---

**Made with ❤️ to help Arizona families manage Empowerment Scholarship Account expenses efficiently**

Last Updated: November 29, 2025
