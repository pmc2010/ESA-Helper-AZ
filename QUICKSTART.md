# ESA Helper - Quick Start Guide

Get up and running with the ESA Helper tool in 5 minutes.

## Prerequisites

- Python 3.11+ (check with `python --version`)
- Chrome browser installed
- Your ClassWallet login credentials handy

## Step 1: Install Dependencies

From the project directory:

```bash
# If using pip
pip install flask selenium pillow

# If using uv (recommended)
uv sync
```

## Step 2: Start the Application

```bash
python main.py
```

You should see:
```
============================================================
ESA Helper - ClassWallet Automation Tool
============================================================

Starting Flask application...
Open your browser and navigate to: http://localhost:5000

Press Ctrl+C to stop the server
```

Your browser should automatically open to http://localhost:5000

## Step 3: Configure Credentials

1. Click the **"Configure Credentials"** button (in the alert at the top)
2. Enter your ClassWallet email and password
3. Click **"Save Credentials"**

Your credentials are stored locally in `config.json` (plaintext, local machine only).

## Step 4: Submit Your First Reimbursement

### For a Reimbursement (payment you already made):

1. **Select Student**: Choose Student A, Student B, or Student C
2. **Request Type**: Select "Reimbursement"
3. **Store Name**: Enter instructor/store name (e.g., "Ice Skating Instructor")
4. **Amount**: Enter the amount you paid
5. **Expense Category**: Select the appropriate category
6. **Upload Documents**: Click "Browse Files" to select required documents
7. **PO Number**: Auto-generates (can edit if needed)
8. **Comment**: Add a note (e.g., "AZ Ice lesson - 2024-11-03")
9. **Review & Submit**: Click to confirm details
10. **Submit to ClassWallet**: Browser opens and submits automatically

### For Direct Pay (payment from account):

⚠️ **NOTE: Direct Pay automation is NOT fully implemented or tested.**

The Direct Pay form is available for data entry, but the full end-to-end submission automation may not work correctly.

**To use Direct Pay:**
1. Follow steps 1-5 above, but select "Direct Pay" instead
2. A **"Pre-Approved Vendor"** dropdown appears
3. Select your vendor (or click "+ Add New Vendor" to add one)
4. Fill in all required fields
5. **Important:** You will need to manually complete the ClassWallet submission

For a fully automated experience, use **Reimbursement** instead, which is fully functional and tested.

See [README.md - Known Limitations](../README.md#known-limitations--important-notes) for more details.

## Step 5: Create a Template (Optional)

Templates save time for repeated submissions. Use the **Manage Templates** page:

1. Go to **Settings > Manage Templates**
2. Select a student from the dropdown
3. Click **+ Add New Template**
4. Fill in template details:
   - Template Name: "Lesson Template A"
   - Vendor: Select from the vendor list (or create a new vendor first)
   - Request Type: "Reimbursement"
   - Amount: $45
   - Expense Category: "Tutoring & Teaching Services - Accredited Individual"
   - Comment: "Lesson - Instructor A - Lesson {yyyy-mm-dd}" (use {yyyy-mm-dd} for auto date)
5. Click **Save Template**

Next time you submit for ice skating, just select this template and it pre-fills the form!

## Step 6: Keep the App Running Continuously (Recommended)

The app should always be available for quick submissions. Follow the instructions for your operating system:

### macOS: Using LaunchAgent

1. **Create the LaunchAgent script:**

   Open Terminal and run:
   ```bash
   mkdir -p ~/Library/LaunchAgents
   ```

2. **Create the plist file:**

   Create a file at `~/Library/LaunchAgents/com.esa-helper.plist`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
     <key>Label</key>
     <string>com.esa-helper.app</string>
     <key>ProgramArguments</key>
     <array>
       <string>/usr/bin/python3</string>
       <string>/path/to/ESA-Helpers/main.py</string>
     </array>
     <key>WorkingDirectory</key>
     <string>/path/to/ESA-Helpers</string>
     <key>StandardOutPath</key>
     <string>/tmp/esa-helper.log</string>
     <key>StandardErrorPath</key>
     <string>/tmp/esa-helper-error.log</string>
     <key>KeepAlive</key>
     <true/>
     <key>RunAtLoad</key>
     <true/>
   </dict>
   </plist>
   ```

   **Important:** Replace `/path/to/ESA-Helpers` with your actual project path (e.g., `/Users/petermandy/Documents/GitHub/ESA-Helpers`)

3. **Load the LaunchAgent:**

   ```bash
   launchctl load ~/Library/LaunchAgents/com.esa-helper.plist
   ```

4. **Verify it's running:**

   ```bash
   launchctl list | grep esa-helper
   ```

5. **The app will now start automatically on login and restart if it crashes.**

**To stop the app:**
```bash
launchctl unload ~/Library/LaunchAgents/com.esa-helper.plist
```

### Windows: Using Task Scheduler

1. **Open Task Scheduler:**
   - Press `Win+R`, type `taskschd.msc`, and press Enter

2. **Create a new task:**
   - Right-click **Task Scheduler Library** → **Create Task**
   - Name: `ESA Helper`
   - Check: "Run whether user is logged in or not"
   - Check: "Run with highest privileges"

3. **Set the Trigger:**
   - Go to **Triggers** tab
   - Click **New**
   - Begin the task: **At startup**
   - Click **OK**

4. **Set the Action:**
   - Go to **Actions** tab
   - Click **New**
   - Action: **Start a program**
   - Program: `C:\path\to\python.exe` (e.g., `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe`)
   - Arguments: `main.py`
   - Start in: `C:\path\to\ESA-Helpers` (your project directory)
   - Click **OK**

5. **Set Conditions:**
   - Go to **Conditions** tab
   - Uncheck "Stop if the computer switches to battery power"
   - Click **OK** to save

6. **Enable auto-restart:**
   - Go to **Settings** tab
   - Check "If the task fails, restart every: 5 minutes"
   - Click **OK**

7. **The app will now start automatically on login and restart if it crashes.**

**To verify it's running:**
- Press `Win+R`, type `localhost:5000`, and press Enter
- You should see the ESA Helper app

### Linux: Using systemd

1. **Create a systemd service file:**

   ```bash
   sudo nano /etc/systemd/system/esa-helper.service
   ```

2. **Add the following content:**

   ```ini
   [Unit]
   Description=ESA Helper Application
   After=network.target

   [Service]
   Type=simple
   User=YOUR_USERNAME
   WorkingDirectory=/path/to/ESA-Helpers
   ExecStart=/usr/bin/python3 /path/to/ESA-Helpers/main.py
   Restart=always
   RestartSec=10
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

   Replace `YOUR_USERNAME` and `/path/to/ESA-Helpers` with your actual values.

3. **Enable and start the service:**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable esa-helper.service
   sudo systemctl start esa-helper.service
   ```

4. **Verify it's running:**

   ```bash
   sudo systemctl status esa-helper.service
   ```

## Quick Restart Link

If the app crashes or stops, anyone can quickly restart it by clicking a bookmark or script:

### macOS: Create a Quick Restart Script

1. **Create a restart script:**

   ```bash
   cat > ~/Desktop/Restart-ESA-Helper.command << 'EOF'
   #!/bin/bash
   launchctl unload ~/Library/LaunchAgents/com.esa-helper.plist
   sleep 2
   launchctl load ~/Library/LaunchAgents/com.esa-helper.plist
   open http://localhost:5000
   EOF
   ```

2. **Make it executable:**

   ```bash
   chmod +x ~/Desktop/Restart-ESA-Helper.command
   ```

3. **Double-click the script to restart** – it will unload, reload, and open the app in your browser

### Windows: Create a Quick Restart Batch File

1. **Create a file called `Restart-ESA-Helper.bat`** on your Desktop:

   ```batch
   @echo off
   taskkill /f /im python.exe >nul 2>&1
   timeout /t 2 /nobreak
   cd C:\path\to\ESA-Helpers
   start python main.py
   timeout /t 3 /nobreak
   start http://localhost:5000
   ```

   Replace `C:\path\to\ESA-Helpers` with your actual project path.

2. **Double-click the batch file to restart** – it will kill Python, restart the app, and open it in your browser

### Browser Bookmark (All Platforms)

Create a bookmark in your browser:
- **Name:** ESA Helper
- **URL:** `http://localhost:5000`

If the app seems unresponsive, try:
1. Click the bookmark to refresh
2. Wait 5 seconds for the page to load
3. If still not working, run the restart script

## File Organization

Your documents should be in this structure (mounted from Synology):

```
/path/to/esa/documents/
├── student_a/2024/
│   ├── receipts/
│   ├── invoices/
│   └── attestations/
├── student_b/2024/
└── student_c/2024/
```

## Required Documents by Category

| Category | Receipt | Invoice | Attestation | Curriculum |
|----------|---------|---------|-------------|------------|
| Computer Hardware | ✓ | | | |
| Curriculum | ✓ | | | |
| Tutoring (Facility) | ✓ | ✓ | | |
| Tutoring (Individual) | ✓ | ✓ | ✓ | |
| Supplemental Materials | ✓ | | | ✓ |

## Troubleshooting

### App won't start
```bash
# Make sure Python 3.11+ is installed
python --version

# Check if port 5000 is in use
lsof -i :5000

# Install missing dependencies
pip install flask selenium pillow
```

### Credentials won't save
- Close and restart the app
- Check that `config.json` was created in the project root
- Try clearing browser cache and cookies

### Files won't upload
- Make sure Synology drive is mounted at `/Volumes/...`
- Check file paths are correct
- Verify file format (PDF, JPG, PNG, GIF)

### ClassWallet automation fails
- Verify credentials are correct
- Try manual submission first to test your account
- Check Chrome browser is installed
- Review terminal output for error messages

## Key Keyboard Shortcuts

- **Ctrl+C**: Stop the Flask server
- **Cmd+Shift+Delete**: Clear form and start over
- **Tab**: Navigate between form fields

## Files & Folders

```
main.py              # Start the app from here
app/
  routes.py          # Form and API endpoints
  classwallet.py     # Selenium automation (with ClassWallet interaction)
  automation.py      # Orchestration layer
  templates/
    index.html       # The web form
    manage-templates.html # Template management page
data/
  students.json      # Student profiles
  vendors.json       # Vendor information
  esa_templates/     # Your saved templates (organized by student)
logs/                # Submission logs
config.json          # Your credentials (local only)
```

## Next Steps

1. ✓ Application running
2. ✓ Credentials configured
3. ✓ Submit your first request
4. Create templates for common submissions
5. Add more vendors to the Direct Pay list

## Support

- Detailed documentation: See [README.md](README.md)
- Workflow details: See [ESA_WORKFLOW.md](ESA_WORKFLOW.md)
- Issues/errors: Check `logs/` directory for submission logs

---

**You're all set!** The app should save you 35+ minutes per submission by automating the ClassWallet form-filling process.
