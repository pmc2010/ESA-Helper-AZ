# ESA Helper - Initial Setup Guide

This guide walks you through setting up ESA Helper for the first time.

## Step 1: Clone the Repository

```bash
git clone https://github.com/pmc2010/ESA-Helpers.git
cd ESA-Helpers
```

## Step 2: Install Dependencies

### Using uv (Recommended)

```bash
uv sync
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install flask selenium pillow
```

## Step 3: Load Sample Data

The repository includes sample data files to help you get started. These are separate from the actual data files to keep your personal information safe.

### Copy Sample Data Files to Active Data Files

**macOS/Linux:**
```bash
cp data/students.sample.json data/students.json
cp data/vendors.sample.json data/vendors.json
cp -r data/esa_templates.sample data/esa_templates
```

**Windows (PowerShell):**
```powershell
Copy-Item data/students.sample.json data/students.json
Copy-Item data/vendors.sample.json data/vendors.json
Copy-Item -Recurse data/esa_templates.sample data/esa_templates
```

**Windows (Command Prompt):**
```batch
copy data\students.sample.json data\students.json
copy data\vendors.sample.json data\vendors.json
xcopy data\esa_templates.sample data\esa_templates /E /I
```

### Customize Sample Data

Now you can edit the copied files with your own data:

1. **Edit `data/students.json`**
   - Replace student names with your actual student names
   - Update addresses
   - Set folder paths where your documents are stored

2. **Edit `data/vendors.json`**
   - Add your instructors/vendors
   - Include their contact information
   - Set business names (leave blank if not applicable)

3. **Edit `data/esa_templates/`**
   - Rename files from `student1.json`, `student2.json`, etc. to match your student IDs
   - Edit template contents to match your vendors and expenses

**Important:** Files in `data/students.json`, `data/vendors.json`, and `data/esa_templates/` are in `.gitignore` and won't be committed to git. Keep your personal information safe!

## Step 4: Test the Application

```bash
python main.py
```

Your browser should automatically open to http://localhost:5000

## Step 5: Configure Credentials

1. Click **"Configure Credentials"** button at the top
2. Enter your ClassWallet email and password
3. Click **"Save Credentials"**

## Step 6: Keep the App Running (Recommended)

Follow the instructions in [QUICKSTART.md - Step 6](QUICKSTART.md#step-6-keep-the-app-running-continuously-recommended) to set up automatic launching on your system.

## File Structure After Setup

After following this guide, your project should look like:

```
ESA-Helpers/
├── data/
│   ├── students.json          ← Your student data
│   ├── vendors.json           ← Your vendor/instructor data
│   ├── esa_templates/         ← Your templates organized by student
│   ├── students.sample.json   ← Sample (do not edit)
│   ├── vendors.sample.json    ← Sample (do not edit)
│   └── esa_templates.sample/  ← Sample (do not edit)
├── app/
├── logs/
├── config.json                ← Your credentials
├── main.py
└── ...
```

## Troubleshooting

### Port 5000 Already in Use

If you get an error that port 5000 is already in use:

```bash
# Find what's using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill the process or use a different port
# To use a different port, edit main.py and change the port parameter
```

### Import Errors

If you get import errors when running `python main.py`:

```bash
# Ensure you're in the virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
uv sync  # or pip install flask selenium pillow
```

### Sample Data Not Copying

Make sure you're in the project root directory:

```bash
pwd  # Show current directory (should end with ESA-Helpers)
ls data/students.sample.json  # Verify file exists
```

## Next Steps

1. ✓ Repository cloned
2. ✓ Dependencies installed
3. ✓ Sample data loaded
4. ✓ App tested
5. Customize with your data
6. Set up automatic launching
7. Start using the app!

See [QUICKSTART.md](QUICKSTART.md) for detailed usage instructions.
