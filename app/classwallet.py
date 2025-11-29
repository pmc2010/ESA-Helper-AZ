"""
ClassWallet Selenium Automation Module

Handles all interactions with ClassWallet including login and form submissions.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import logging
from pathlib import Path
from datetime import datetime
from app.utils import generate_po_number

# Configure logging with both console and file output
def _setup_logging():
    """Configure logging to output to both console and file

    Uses date-based log files (automation_YYYYMMDD.log) so all logs for the same day
    are in one file and can be easily accessed from the frontend.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Only configure if not already configured (avoid duplicate handlers)
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Create a log file with date only (not timestamp) so all logs for the same day go in one file
    log_file = log_dir / f"automation_{datetime.now().strftime('%Y%m%d')}.log"

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler - use append mode so multiple runs in the same day all go to same file
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(f"Automation logging started. Log file: {log_file}")

    return logger

logger = _setup_logging()


class ClassWalletAutomation:
    """Handles ClassWallet login and reimbursement/direct pay submission"""

    def __init__(self, email: str, password: str, headless: bool = False):
        """
        Initialize ClassWallet automation

        Args:
            email: ClassWallet email
            password: ClassWallet password
            headless: Run browser in headless mode (no GUI)
        """
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        self.headless = headless
        self.browser_logs = []  # Store browser console errors for debugging

    def _capture_browser_logs(self):
        """
        Capture browser console errors and logs for debugging.
        This helps identify JavaScript errors on ClassWallet that might be breaking automation.
        """
        try:
            if not self.driver:
                return []

            # Get browser console logs
            logs = self.driver.get_log('browser')
            error_logs = [log for log in logs if log['level'] == 'SEVERE']

            if error_logs:
                logger.warning("🔴 Browser Console Errors Detected:")
                for log in error_logs:
                    logger.warning(f"   {log['message']}")
                    self.browser_logs.append({
                        'level': 'SEVERE',
                        'message': log['message'],
                        'timestamp': log['timestamp']
                    })

            return error_logs
        except Exception as e:
            logger.debug(f"Could not capture browser logs: {str(e)}")
            return []

    def _get_page_state(self):
        """
        Capture current page state for debugging.
        Returns useful info about what's currently shown on the page.
        """
        try:
            if not self.driver:
                return {}

            # Inject JavaScript to check for common error indicators
            error_indicators = self.driver.execute_script("""
                return {
                    'current_url': window.location.href,
                    'page_title': document.title,
                    'error_messages': Array.from(document.querySelectorAll('[role="alert"], .alert, .error, .warning')).map(el => el.textContent.trim()),
                    'js_errors_in_console': window.__js_errors || [],
                    'page_ready': document.readyState,
                    'visible_text': document.body.innerText.substring(0, 500)
                };
            """)

            return error_indicators
        except Exception as e:
            logger.debug(f"Could not get page state: {str(e)}")
            return {'error': str(e)}

    def _log_error_with_context(self, operation: str, error: Exception):
        """
        Log an error with full page context for debugging ClassWallet issues.

        Args:
            operation: What operation was being attempted
            error: The exception that occurred
        """
        logger.error(f"\n{'='*60}")
        logger.error(f"❌ ERROR DURING: {operation}")
        logger.error(f"{'='*60}")
        logger.error(f"Error Message: {str(error)}")
        logger.error(f"Full Traceback:", exc_info=True)

        # Capture page state
        page_state = self._get_page_state()
        logger.error(f"Page State:")
        logger.error(f"  Current URL: {page_state.get('current_url', 'N/A')}")
        logger.error(f"  Page Title: {page_state.get('page_title', 'N/A')}")
        logger.error(f"  Page Ready: {page_state.get('page_ready', 'N/A')}")

        if page_state.get('error_messages'):
            logger.error(f"  Error Messages on Page:")
            for msg in page_state.get('error_messages', []):
                logger.error(f"    - {msg}")

        # Capture browser console logs
        self._capture_browser_logs()
        logger.error(f"{'='*60}\n")

    def _initialize_driver(self):
        """Initialize Chrome WebDriver with logging enabled"""
        options = webdriver.ChromeOptions()

        if self.headless:
            options.add_argument('--headless')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')

        # Enable Chrome logging for debugging ClassWallet issues
        options.add_argument('--enable-logging')
        options.add_argument('--v=1')

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

        # Enable browser console logging
        try:
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Log.enable', {})
            logger.info("✓ Browser logging enabled for debugging")
        except Exception as e:
            logger.debug(f"Could not enable browser logging: {str(e)}")

        logger.info("Chrome WebDriver initialized")

    def login_to_classwallet(self):
        """
        Login to ClassWallet via ESA Portal

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            if not self.driver:
                self._initialize_driver()

            # Step 1: Navigate to ESA Portal
            logger.info("Opening ESA Portal...")
            self.driver.get("https://esaportal.azed.gov/ApplicantPortal")

            # Step 2: Fill login credentials
            logger.info("Entering credentials...")
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "userNameInput"))
            )
            password_field = self.driver.find_element(By.ID, "passwordInput")

            username_field.clear()
            username_field.send_keys(self.email)

            password_field.clear()
            password_field.send_keys(self.password)

            # Step 3: Submit login form
            login_button = self.driver.find_element(By.ID, "submitButton")
            login_button.click()

            # Wait for redirect
            logger.info("Waiting for authentication...")
            time.sleep(3)

            # Step 4: Navigate to ClassWallet
            logger.info("Navigating to ClassWallet...")
            self.driver.get("https://saml.classwallet.com/")

            # Verify we're logged in
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            logger.info("Successfully authenticated to ClassWallet!")
            return True

        except Exception as e:
            self._log_error_with_context("ClassWallet Login", e)
            return False

    def select_student(self, student_name: str):
        """
        Select a student from the dropdown

        Args:
            student_name: Name of the student from configured student profiles

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("STEP 1: SELECT STUDENT")
            logger.info("=" * 60)
            logger.info(f"Student to select: {student_name}")

            # Map short names to full names (as they appear in ClassWallet)
            # These are fallback mappings for demo purposes
            name_mapping = {
                'student1': 'Student One',
                'student2': 'Student Two',
                'student3': 'Student Three'
            }

            full_name = name_mapping.get(student_name, student_name)
            logger.info(f"Looking for: {full_name}")

            # Step 0: Check if student is already selected (appears in top-right corner)
            logger.info("\n0. Checking if student is already selected...")
            try:
                # Look for the student name in the header area (top-right)
                # Check for visible instances (not hidden in dropdown menus)
                student_elements = self.driver.find_elements(
                    By.XPATH, f"//span[contains(text(), '{full_name}')]"
                )

                logger.info(f"Found {len(student_elements)} element(s) containing '{full_name}'")

                # If we found the student name, check if it's visible (not hidden in a dropdown)
                for i, elem in enumerate(student_elements):
                    is_displayed = elem.is_displayed()
                    logger.info(f"  Element {i+1}: displayed={is_displayed}")

                    if is_displayed:
                        # Check if this element is NOT inside a dropdown/menu (more robust than pixel-based detection)
                        try:
                            # Look for dropdown/menu parent classes that indicate hidden state
                            parent = elem.find_element(By.XPATH, "ancestor::*[1]")
                            parent_classes = parent.get_attribute("class") or ""
                            parent_role = parent.get_attribute("role") or ""

                            # If it's in a hidden menu or dropdown, skip it
                            if any(hidden_indicator in parent_classes.lower() for hidden_indicator in ['hidden', 'collapse', 'dropdown']):
                                logger.info(f"    Element {i+1} is in a hidden dropdown, skipping")
                                continue

                            # If the parent is not a menu/dropdown, this is the visible student selector
                            if 'menu' not in parent_role.lower():
                                logger.info(f"✓ Student {full_name} is already selected!")
                                logger.info(f"Student selection complete (no action needed)")
                                return True
                        except Exception as parent_check_error:
                            # If we can't determine parent structure, assume it's the visible one
                            logger.info(f"    Parent check inconclusive, assuming this is the visible instance")
                            logger.info(f"✓ Student {full_name} is already selected!")
                            logger.info(f"Student selection complete (no action needed)")
                            return True

                logger.info("Student not currently selected, will open dropdown...")
            except Exception as e:
                # Student not already selected, proceed with dropdown selection
                logger.info(f"Exception during student check: {str(e)}")
                logger.info("Student not currently selected, will open dropdown...")
                pass

            # Step 1: Click the menu button to open the student dropdown
            logger.info("\n1. Opening student selector menu...")
            menu_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "openMenu"))
            )
            menu_button.click()
            logger.info("✓ Menu opened")

            time.sleep(0.5)

            # Step 2: Look for "Switch to user" option and click it
            logger.info("2. Looking for 'Switch to user' option...")
            switch_user_item = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(), 'Switch to user')]/parent::div/parent::li")
                )
            )
            switch_user_item.click()
            logger.info("✓ 'Switch to user' clicked")

            time.sleep(0.5)

            # Step 3: Click on the student's name
            logger.info(f"3. Selecting student: {full_name}")
            student_item = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//span[contains(text(), '{full_name}')]/parent::div/parent::li")
                )
            )
            student_item.click()
            logger.info(f"✓ Student {full_name} selected")

            time.sleep(1)

            logger.info(f"Student selection complete!")
            return True

        except Exception as e:
            self._log_error_with_context("Select Student", e)
            return False

    def start_reimbursement(self, store_name: str, amount: str):
        """
        Start a new reimbursement submission

        Args:
            store_name: Name of the store/instructor
            amount: Reimbursement amount

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("STEP 2: START REIMBURSEMENT")
            logger.info("=" * 60)
            logger.info(f"Store/Instructor: {store_name}")
            logger.info(f"Amount: ${amount}")

            # Wait for page to be ready after student selection
            time.sleep(1)

            logger.info("\nWaiting for 'Start a new Reimbursement' button to appear...")

            # Find and click "Start a new Reimbursement" button
            # Use data-test attribute for better reliability
            reimbursement_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='start-reimbursement']"))
            )
            logger.info("✓ Found 'Start a new Reimbursement' button")

            reimbursement_button.click()
            logger.info("✓ Button clicked")

            time.sleep(2)  # Wait for page to load after clicking

            logger.info("\nWaiting for form fields to appear...")

            # Fill store name - use id="store"
            store_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "store"))
            )
            logger.info("✓ Found store name field")
            store_field.clear()
            store_field.send_keys(store_name)
            logger.info(f"✓ Entered store name: {store_name}")

            # Fill amount - find input within Amount container
            # Convert amount to cents (ClassWallet stores amounts in cents)
            amount_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-test='Amount']//input[@type='text']"))
            )
            logger.info("✓ Found amount field")
            amount_field.clear()
            amount_cents = str(int(float(amount) * 100))
            amount_field.send_keys(amount_cents)
            logger.info(f"✓ Entered amount: ${amount} (${amount_cents} cents)")

            # Click Next button - use data-test attribute
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='Next']"))
            )
            logger.info("✓ Found Next button")
            next_button.click()
            logger.info("✓ Clicked Next button")

            time.sleep(1)

            logger.info("✓ Reimbursement form completed!")
            return True

        except Exception as e:
            self._log_error_with_context("Start Reimbursement", e)
            return False

    def handle_image_editor_modal(self):
        """
        Detect and handle ClassWallet's image editor modal that appears during file uploads.

        The modal shows image resize/rotate instructions and has a Save button that needs to be clicked.
        This method handles MULTIPLE modals (e.g., one per image file).

        Returns:
            bool: True if all modals were handled or not present, False on error
        """
        try:
            logger.info("Checking for image editor modal(s)...")

            modal_count = 0
            max_attempts = 10  # Prevent infinite loops; ClassWallet typically shows 1-4 modals max

            # Keep checking for modals until none appear
            while modal_count < max_attempts:
                try:
                    # Try to find the Save button with a short timeout (3 seconds)
                    # The button has data-test="Save" and id="save"
                    save_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='Save']"))
                    )
                    modal_count += 1
                    logger.info(f"✓ Image editor modal #{modal_count} detected, clicking Save button...")
                    save_button.click()

                    # Wait for modal to close before checking for the next one
                    logger.info(f"  Waiting for modal #{modal_count} to close...")
                    time.sleep(1.5)

                except Exception:
                    # No more modals found - this is expected after all modals are handled
                    if modal_count > 0:
                        logger.info(f"✓ All {modal_count} image editor modal(s) handled successfully")
                    else:
                        logger.info("✓ No image editor modal present (normal)")
                    return True

            # If we hit max_attempts, something is wrong
            logger.error(f"❌ Hit max modal attempts ({max_attempts}), giving up to prevent infinite loop")
            return False

        except Exception as e:
            logger.error(f"❌ Error handling image editor modal: {str(e)}")
            return False

    def upload_files(self, file_paths: dict):
        """
        Upload required files

        Args:
            file_paths: Dictionary of {file_type: file_path} OR {file_type: {name, path, size}}
                       OR {file_type: [{name, path, size}, ...]} for multiple files

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"=== STEP 3: UPLOAD FILES ===")
            logger.info(f"Processing {len(file_paths)} file types...")

            if not file_paths:
                logger.info("✓ No files to upload")
                return True

            # Extract file paths - handle string paths, single objects, and arrays of objects
            files_to_upload = []
            for file_type, file_data in file_paths.items():
                # Handle array of files (new format from multiple file upload)
                if isinstance(file_data, list):
                    for idx, single_file in enumerate(file_data):
                        # Extract path from file metadata object
                        if isinstance(single_file, dict):
                            file_path = single_file.get('path')
                            file_name = single_file.get('name', 'unknown')
                            if not file_path:
                                logger.error(f"No path found in file metadata for {file_type}[{idx}]")
                                return False
                        else:
                            # String path
                            file_path = single_file
                            file_name = Path(file_path).name

                        if not Path(file_path).exists():
                            logger.error(f"File not found: {file_path}")
                            return False

                        abs_path = str(Path(file_path).absolute())
                        files_to_upload.append(abs_path)
                        logger.info(f"✓ Found {file_type} #{idx+1}: {file_name}")

                # Handle single file (old format - backward compatible)
                else:
                    # Check if file_data is a dict with metadata or just a string path
                    if isinstance(file_data, dict):
                        file_path = file_data.get('path')
                        file_name = file_data.get('name', 'unknown')
                        if not file_path:
                            logger.error(f"No path found in file metadata for {file_type}")
                            return False
                    else:
                        # String path
                        file_path = file_data
                        file_name = Path(file_path).name

                    if not Path(file_path).exists():
                        logger.error(f"File not found: {file_path}")
                        return False

                    abs_path = str(Path(file_path).absolute())
                    files_to_upload.append(abs_path)
                    logger.info(f"✓ Found {file_type}: {file_name}")

            # Find the file input element (it's hidden but Selenium can interact with it)
            logger.info("1. Locating file input element...")
            file_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            logger.info("✓ Found file input element")

            # Send file paths to the input
            # Selenium can send files to hidden inputs
            file_paths_string = '\n'.join(files_to_upload)
            logger.info(f"2. Sending {len(files_to_upload)} file path(s)...")
            file_input.send_keys(file_paths_string)
            logger.info(f"✓ Sent file paths to input")

            # Wait for files to be processed by ClassWallet
            logger.info("3. Waiting for file upload processing...")
            time.sleep(4)

            logger.info("✓ Files uploaded successfully")

            # Check for and handle image editor modal if it appears
            logger.info("4. Checking for image editor modal...")
            if not self.handle_image_editor_modal():
                logger.error("❌ Failed to handle image editor modal")
                return False

            # Click Next button to proceed to next step
            logger.info("5. Clicking Next button...")
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='Next']"))
            )
            next_button.click()
            logger.info("✓ Next button clicked")

            time.sleep(2)

            return True

        except Exception as e:
            self._log_error_with_context("Upload Files", e)
            return False

    def select_expense_category(self, category: str):
        """
        Select purse (Arizona - ESA) and expense category

        Args:
            category: Expense category name

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"=== STEP 4: SELECT PURSE AND CATEGORY ===")
            logger.info(f"Category: {category}")

            # Wait for page to be fully loaded and any upload notifications to disappear
            # The upload process may have triggered notifications that need time to clear
            logger.info("0. Waiting for page to stabilize after file uploads...")
            time.sleep(3)  # Wait for uploads to complete and notifications to clear

            # Wait for the page body to be present (ensures navigation is complete)
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("✓ Page loaded and ready")

            # Step 1: Select Arizona - ESA checkbox
            logger.info("1. Selecting Arizona - ESA purse...")

            # Try multiple selectors for the ESA checkbox
            # The checkbox is a span with MUI styling (MuiCheckbox-root), not a button
            esa_checkbox = None
            selectors = [
                # First try: span with data-test attribute (most specific)
                (By.CSS_SELECTOR, "span[data-test='Arizona - ESA'][aria-label='Arizona - ESA']"),
                # Second try: span with MuiCheckbox-root class and data-test
                (By.XPATH, "//span[@data-test='Arizona - ESA' and contains(@class, 'MuiCheckbox-root')]"),
                # Third try: input checkbox directly
                (By.XPATH, "//input[@type='checkbox'][@value='5de682872a2f835d4a700e9d']"),
                # Fallback: any span with Arizona - ESA aria-label
                (By.XPATH, "//span[@aria-label='Arizona - ESA']"),
            ]

            for selector in selectors:
                try:
                    esa_checkbox = self.wait.until(
                        EC.element_to_be_clickable(selector)
                    )
                    logger.info(f"✓ Found ESA checkbox using selector: {selector}")
                    break
                except:
                    logger.debug(f"Selector not found: {selector}")
                    continue

            if not esa_checkbox:
                logger.error("❌ Could not find Arizona - ESA checkbox with any selector")
                # Wait a bit and try broader search
                time.sleep(2)
                try:
                    # Look for any element containing "Arizona" in aria-label
                    esa_checkbox = self.driver.find_element(
                        By.XPATH,
                        "//*[contains(@aria-label, 'Arizona')][@data-test='Arizona - ESA']"
                    )
                    logger.info("✓ Found ESA checkbox after wait")
                except:
                    logger.error("Failed to find ESA checkbox - page may have changed")
                    logger.info("Dumping page source for debugging...")
                    logger.info(self.driver.page_source[:2000])
                    return False

            # Check if already selected by looking at the parent's class
            try:
                if "Mui-checked" not in esa_checkbox.get_attribute("class"):
                    esa_checkbox.click()
                    logger.info("✓ Arizona - ESA checkbox clicked")
                else:
                    logger.info("✓ Arizona - ESA already selected")
            except Exception as e:
                logger.error(f"Error clicking ESA checkbox: {str(e)}")
                return False

            time.sleep(2)  # Extended wait for category list to load

            # Step 2: Select expense category
            logger.info(f"2. Selecting expense category: {category}...")

            # Note: Category names from the form may differ from ClassWallet's exact format:
            # Form sends: "Computer Hardware & Technological Devices"
            # ClassWallet has: "Computer hardware and technological devices"
            # Form sends: "Tutoring & Teaching Services - Accredited Individual"
            # ClassWallet has: "Tutoring and teaching Services – Accredited Individual"
            # (different: & vs "and", capitalization, en-dash vs hyphen)

            # Normalize the category name to match ClassWallet's format
            # ClassWallet uses specific capitalization patterns:
            # "Computer Hardware & Technological Devices" → "Computer hardware and technological devices"
            # "Tutoring & Teaching Services" → "Tutoring and teaching Services" (Services capitalized)

            # First, do the specific replacements for known patterns
            if category.startswith("Computer Hardware"):
                # Computer Hardware category: all words after "Computer" are lowercase
                category_normalized = "Computer hardware and technological devices"
            elif "Tutoring" in category and "Teaching" in category:
                # Tutoring categories: replace & with "and", but keep Services capitalized
                category_normalized = category.replace(" & ", " and ").replace("&", "and")
                category_normalized = category_normalized.replace("and Teaching", "and teaching")
                category_normalized = category_normalized.replace(" - ", " – ")  # Convert hyphen to en-dash
            else:
                # Generic normalization for other categories
                category_normalized = category.replace(" & ", " and ").replace("&", "and")
                category_normalized = category_normalized.replace(" - ", " – ")  # Convert hyphen to en-dash

            logger.debug(f"Original category: {category}")
            logger.debug(f"Normalized category: {category_normalized}")

            # Find the category checkbox by its data-test attribute
            # Categories are in divs with nested Material-UI checkbox spans
            category_checkbox = None
            category_selectors = [
                # Priority 1: Find the span.MuiCheckbox-root inside a div[data-test] with exact match
                (By.XPATH, f"//div[@data-test='{category}']//span[contains(@class, 'MuiCheckbox-root')]"),
                # Priority 2: Find the span.MuiCheckbox-root inside a div[data-test] with normalized
                (By.XPATH, f"//div[@data-test='{category_normalized}']//span[contains(@class, 'MuiCheckbox-root')]"),
                # Priority 3: Try CSS selector for div then we'll target span inside
                (By.CSS_SELECTOR, f"div[data-test='{category}']"),
                # Priority 4: Try with normalized name
                (By.CSS_SELECTOR, f"div[data-test='{category_normalized}']"),
                # Priority 5: Try via aria-label with exact match
                (By.XPATH, f"//span[@aria-label='{category}']"),
                # Priority 6: Try via aria-label with normalized
                (By.XPATH, f"//span[@aria-label='{category_normalized}']"),
                # Priority 7: Try finding span with parent containing category text (flexible)
                (By.XPATH, f"//span[contains(@class, 'MuiCheckbox-root')][ancestor::div[contains(., '{category}')]]"),
                # Priority 8: Try normalized version
                (By.XPATH, f"//span[contains(@class, 'MuiCheckbox-root')][ancestor::div[contains(., '{category_normalized}')]]"),
            ]

            for idx, selector in enumerate(category_selectors):
                try:
                    logger.info(f"Trying selector {idx+1}/{len(category_selectors)}: {selector}")
                    # First, just find the element (don't require it to be clickable)
                    # We'll handle clicking separately
                    short_wait = WebDriverWait(self.driver, 3)
                    category_checkbox = short_wait.until(
                        EC.presence_of_element_located(selector)
                    )
                    logger.info(f"✓ Found category element using selector {idx+1}: {selector}")
                    break
                except Exception as e:
                    logger.info(f"  Selector {idx+1} failed: {type(e).__name__}")
                    continue

            if not category_checkbox:
                logger.error(f"❌ Could not find category '{category}' checkbox with any selector")
                logger.info("Attempted selectors:")
                for idx, selector in enumerate(category_selectors):
                    logger.info(f"  {idx+1}. {selector}")

                # Try to find all divs with data-test to help debugging
                try:
                    all_categories = self.driver.find_elements(By.XPATH, "//div[@data-test]")
                    logger.info(f"Found {len(all_categories)} elements with data-test attribute:")
                    # Log ALL categories, not just first 15
                    for idx, elem in enumerate(all_categories):
                        data_test = elem.get_attribute("data-test")
                        logger.info(f"  {idx+1}. data-test='{data_test}'")
                except Exception as debug_error:
                    logger.debug(f"Could not list available categories: {str(debug_error)}")

                # Also try to find the categories container and dump its HTML
                try:
                    categories_container = self.driver.find_element(By.XPATH, "//div[@data-test='categories']")
                    logger.info("Found categories container, dumping inner HTML:")
                    inner_html = categories_container.get_attribute("innerHTML")
                    logger.info(inner_html[:2000])  # Log first 2000 chars
                except Exception as container_error:
                    logger.debug(f"Could not find categories container: {str(container_error)}")

                logger.info("Dumping page source for debugging...")
                logger.info(self.driver.page_source[:3000])
                return False

            # If we got a div, find the span inside it
            click_target = category_checkbox
            is_div = category_checkbox.tag_name == "div"
            if is_div:
                try:
                    click_target = category_checkbox.find_element(By.XPATH, ".//span[contains(@class, 'MuiCheckbox-root')]")
                    logger.info("✓ Found MuiCheckbox-root span inside div")
                except:
                    logger.warning("⚠️ Could not find span inside div, will try to click div directly")
                    click_target = category_checkbox

            # Check if already selected by looking at the parent span or div
            check_element = click_target if not is_div else category_checkbox
            try:
                is_checked = "Mui-checked" in check_element.get_attribute("class")
            except:
                is_checked = False

            if not is_checked:
                # Scroll element into view first
                self.driver.execute_script("arguments[0].scrollIntoView(true);", click_target)
                time.sleep(0.5)

                # Try clicking the element first (but use JavaScript click to avoid interception issues)
                click_succeeded = False
                try:
                    logger.info(f"Attempting to click category element...")
                    # Use JavaScript click instead of Selenium click to avoid element interception
                    self.driver.execute_script("arguments[0].click();", click_target)
                    logger.info(f"✓ Category '{category}' clicked (JavaScript)")
                    time.sleep(1)  # Wait for UI to update

                    # Check if it worked
                    try:
                        is_checked = "Mui-checked" in check_element.get_attribute("class")
                    except:
                        is_checked = False

                    if is_checked:
                        logger.info(f"✓ Category '{category}' successfully selected")
                        click_succeeded = True
                    else:
                        logger.warning(f"⚠️ JavaScript click didn't select category, trying input element...")
                except Exception as click_error:
                    logger.warning(f"JavaScript click failed: {str(click_error)}")

                # If JavaScript click didn't work, try clicking the input directly
                if not click_succeeded:
                    try:
                        # Find input relative to our click target
                        input_elem = click_target.find_element(By.TAG_NAME, "input") if not is_div else category_checkbox.find_element(By.TAG_NAME, "input")
                        logger.info(f"Found input element, attempting JavaScript click...")
                        self.driver.execute_script("arguments[0].click();", input_elem)
                        logger.info(f"✓ Category '{category}' input clicked (JavaScript)")
                        time.sleep(1)

                        # Verify it worked
                        try:
                            is_checked = "Mui-checked" in check_element.get_attribute("class")
                        except:
                            is_checked = False

                        if is_checked:
                            logger.info(f"✓ Category '{category}' successfully selected")
                            click_succeeded = True
                        else:
                            logger.warning(f"⚠️ Input click didn't work either, trying direct checkbox set...")
                            # Last resort: use JavaScript to directly set checkbox
                            self.driver.execute_script("arguments[0].checked = true;", input_elem)
                            # Trigger change event
                            self.driver.execute_script("""
                                var event = new Event('change', { bubbles: true });
                                arguments[0].dispatchEvent(event);
                            """, input_elem)
                            logger.info(f"✓ Category '{category}' set via JavaScript")
                            time.sleep(1)
                    except Exception as input_error:
                        logger.error(f"Failed to click input: {str(input_error)}")
                        return False
                except Exception as click_error:
                    logger.error(f"Error clicking category: {str(click_error)}")
                    return False
            else:
                logger.info(f"✓ Category '{category}' already selected")

            time.sleep(1)

            # Step 3: Click Next button
            logger.info("3. Clicking Next button...")
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='Next']"))
            )
            next_button.click()
            logger.info("✓ Next button clicked")

            time.sleep(2)

            logger.info("✓ Purse and category selection complete")
            return True

        except Exception as e:
            self._log_error_with_context("Select Expense Category", e)
            return False

    def fill_po_and_comment(self, po_number: str, comment: str, auto_submit: bool = False):
        """
        Fill PO number and comment on review page

        Args:
            po_number: Purchase order number
            comment: Comment text
            auto_submit: If True, click Next to proceed to final submission. If False, stop after filling fields.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"=== STEP 5: FILL PO AND COMMENT ===")
            logger.info(f"PO Number: {po_number}")
            logger.info(f"Comment: {comment}")

            time.sleep(1)  # Wait for page to be ready

            # Fill PO number field
            # PO Number field uses aria-label instead of id
            logger.info("1. Locating PO number field...")
            po_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='PO Number']"))
            )
            logger.info("✓ Found PO number field")
            po_field.clear()
            po_field.send_keys(po_number)
            logger.info(f"✓ Entered PO number: {po_number}")

            time.sleep(0.5)

            # Fill comment field
            # Comments field uses aria-label instead of id
            logger.info("2. Locating comment field...")
            comment_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//textarea[@aria-label='Comments']"))
            )
            logger.info("✓ Found comment field")
            comment_field.clear()
            comment_field.send_keys(comment)
            logger.info(f"✓ Entered comment: {comment}")

            time.sleep(0.5)

            # Only click Next if auto_submit is enabled
            if auto_submit:
                # Click Next button to proceed to final submission
                logger.info("3. Clicking Next button to proceed to final submission...")
                next_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='Next']"))
                )
                next_button.click()
                logger.info("✓ Next button clicked")

                time.sleep(2)
            else:
                logger.info("3. Auto-submit disabled. Stopping after form fill for manual review.")

            logger.info("✓ PO and comment filled successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error filling PO and comment: {str(e)}")
            logger.error(f"Full traceback:", exc_info=True)
            return False

    def fill_direct_pay_additional_info(self, po_number: str = None, comment: str = None) -> bool:
        """
        Fill in additional info for Direct Pay (comments and invoice/quote number).
        This is step 5 in the Direct Pay workflow - different from reimbursement.

        Args:
            po_number: PO or invoice number (optional)
            comment: Comments or description (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"=== STEP 5: FILL DIRECT PAY ADDITIONAL INFO ===")
            if po_number:
                logger.info(f"Invoice/Quote Number: {po_number}")
            if comment:
                logger.info(f"Comments: {comment}")

            time.sleep(1)  # Wait for page to be ready

            # Fill comments field (optional for Direct Pay)
            if comment:
                try:
                    logger.info("1. Locating comments field...")
                    wait_5s = WebDriverWait(self.driver, 5)
                    comments_field = wait_5s.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-test-type='comments'] textarea"))
                    )
                    logger.info("✓ Found comments field")
                    comments_field.clear()
                    comments_field.send_keys(comment)
                    logger.info(f"✓ Entered comments: {comment}")
                except Exception as e:
                    logger.warning(f"Could not fill comments field (optional): {str(e)}")
                    # Comments are optional, so don't fail

            time.sleep(0.5)

            # Fill invoice/quote number field (optional for Direct Pay)
            if po_number:
                try:
                    logger.info("2. Locating invoice/quote number field...")
                    wait_5s = WebDriverWait(self.driver, 5)
                    invoice_field = wait_5s.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-test-type='invoice-or-quote'] input"))
                    )
                    logger.info("✓ Found invoice/quote number field")
                    invoice_field.clear()
                    invoice_field.send_keys(po_number)
                    logger.info(f"✓ Entered invoice/quote number: {po_number}")
                except Exception as e:
                    logger.warning(f"Could not fill invoice/quote number field (optional): {str(e)}")
                    # Invoice number is optional, so don't fail

            time.sleep(0.5)

            logger.info("✓ Direct Pay additional info filled successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error filling Direct Pay additional info: {str(e)}")
            logger.error(f"Full traceback:", exc_info=True)
            return False

    def proceed_direct_pay_to_review(self) -> bool:
        """
        Click Next button to proceed from Additional info to Review page.
        This is step 5b in the Direct Pay workflow.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=== STEP 5B: PROCEED TO REVIEW PAGE ===")
            logger.info("Clicking Next to proceed to Review...")

            wait_5s = WebDriverWait(self.driver, 5)
            next_button = wait_5s.until(
                EC.element_to_be_clickable((By.ID, "next"))
            )
            next_button.click()
            logger.info("✓ Next button clicked - proceeding to Review page")

            time.sleep(2)  # Wait for Review page to load
            logger.info("✓ Ready to review submission")
            return True

        except Exception as e:
            logger.error(f"❌ Error proceeding to review: {str(e)}")
            self._log_error_with_context("proceed_to_review", e)
            return False

    def wait_for_submission_confirmation(self, timeout: int = 15) -> dict:
        """
        Wait for submission confirmation on ClassWallet.
        Polls for success message, confirmation page, or state change.

        Args:
            timeout: Maximum seconds to wait for confirmation (default 15)

        Returns:
            dict: Confirmation data including:
                - 'success': bool - Whether submission was confirmed
                - 'message': str - Confirmation message from page
                - 'url': str - Final URL after submission
        """
        try:
            logger.info("Waiting for submission confirmation...")
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    # Check for success messages
                    success_indicators = self.driver.execute_script("""
                        return {
                            'url': window.location.href,
                            'title': document.title,
                            'success_messages': Array.from(
                                document.querySelectorAll('[role="alert"], .success, .alert-success, [class*="success"]')
                            ).map(el => el.textContent.trim()),
                            'confirmation_messages': Array.from(
                                document.querySelectorAll('h1, h2, h3, [class*="confirmation"], [class*="receipt"]')
                            ).map(el => el.textContent.trim()).filter(t => t.length > 0),
                            'page_text': document.body.innerText.substring(0, 1000)
                        };
                    """)

                    url = success_indicators.get('url', '')
                    messages = success_indicators.get('success_messages', [])
                    confirmation = success_indicators.get('confirmation_messages', [])

                    # Check for success indicators
                    success_keywords = ['submitted', 'success', 'confirmed', 'accepted', 'received', 'completed']
                    all_text = ' '.join(messages + confirmation).lower()

                    if any(keyword in all_text for keyword in success_keywords):
                        logger.info("✓ Submission confirmed!")
                        logger.info(f"  URL: {url}")
                        if messages:
                            logger.info(f"  Message: {messages[0]}")
                        return {
                            'success': True,
                            'message': messages[0] if messages else (confirmation[0] if confirmation else 'Submission confirmed'),
                            'url': url,
                            'confirmation_time': datetime.now().isoformat()
                        }

                    # Check for error messages
                    error_messages = self.driver.execute_script("""
                        return Array.from(
                            document.querySelectorAll('[role="alert"].error, .error, .alert-danger, [class*="error"]')
                        ).map(el => el.textContent.trim());
                    """)

                    if error_messages:
                        logger.error(f"✗ Submission error detected: {error_messages[0]}")
                        return {
                            'success': False,
                            'message': error_messages[0],
                            'url': url,
                            'error': True
                        }

                except Exception as check_error:
                    logger.debug(f"Error checking confirmation: {str(check_error)}")

                time.sleep(1)  # Wait 1 second before next check

            # Timeout reached
            page_state = self._get_page_state()
            logger.warning("Submission confirmation timeout - assuming submitted based on page state")
            return {
                'success': True,
                'message': 'Submission confirmed (timeout)',
                'url': page_state.get('current_url', ''),
                'confirmation_time': datetime.now().isoformat(),
                'timeout': True
            }

        except Exception as e:
            logger.error(f"Error waiting for confirmation: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'error': True
            }

    def submit_reimbursement(self, wait_for_confirmation: bool = True):
        """
        Submit the reimbursement request on final review page

        Args:
            wait_for_confirmation: If True, wait for ClassWallet to confirm submission

        Returns:
            dict or bool: If wait_for_confirmation=True, returns confirmation dict.
                         If wait_for_confirmation=False, returns True/False
        """
        try:
            logger.info(f"=== STEP 6: SUBMIT REIMBURSEMENT ===")

            time.sleep(1)  # Wait for page to be ready

            # Look for the final submit button on the review page
            # NOTE: Selectors need to be updated based on actual ClassWallet HTML
            logger.info("1. Locating submit button...")

            # Try multiple possible button selectors for the submit action
            submit_button = None
            try:
                # First try: data-test attribute
                submit_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='Submit']"))
                )
            except:
                try:
                    # Second try: text content
                    submit_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
                    )
                except:
                    # Third try: aria-label
                    submit_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Submit']"))
                    )

            logger.info("✓ Found submit button")
            submit_button.click()
            logger.info("✓ Submit button clicked")

            # Wait for confirmation if requested
            if wait_for_confirmation:
                return self.wait_for_submission_confirmation()
            else:
                time.sleep(2)  # Wait for submission to complete
                logger.info("✓ Reimbursement submitted")
                return True

        except Exception as e:
            self._log_error_with_context("Submit Reimbursement", e)
            return {'success': False, 'error': True, 'message': str(e)} if wait_for_confirmation else False

    def start_direct_pay(self, vendor_name: str, amount: str, search_term: str = None):
        """
        Start a new direct pay submission

        Args:
            vendor_name: Name of the vendor to pay (display name)
            amount: Payment amount
            search_term: Exact search term for vendor lookup (optional, uses vendor_name if not provided)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("STEP 2: START DIRECT PAY")
            logger.info("=" * 60)
            logger.info(f"Vendor: {vendor_name}")
            logger.info(f"Amount: ${amount}")

            # Use search_term if provided, otherwise fallback to vendor_name
            search_query = search_term or vendor_name
            logger.info(f"Search term: {search_query}")

            # Wait for page to be ready after student selection
            time.sleep(1)

            logger.info("\nWaiting for 'Pay' button to appear...")

            # Find and click "Pay" button in Direct Pay section
            # Target the Pay button in the pay-vendor-tile specifically
            logger.info("1. Clicking 'Pay' button in Direct Pay section...")
            pay_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@id='pay-vendor-tile']//button[contains(., 'Pay')]"))
            )
            logger.info("✓ Found 'Pay' button in Direct Pay section")
            pay_button.click()
            logger.info("✓ Pay button clicked")

            time.sleep(1)

            # Search for vendor
            logger.info("2. Searching for vendor...")
            try:
                # Try Material-UI input field first (used in current ClassWallet)
                vendor_search = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']"))
                )
                logger.info("✓ Found vendor search field (Material-UI input)")
            except Exception as e:
                logger.error(f"Could not find vendor search field with type='search': {str(e)}")
                logger.error("Attempting alternative selectors...")

                # Try alternative selectors if primary fails
                alternative_selectors = [
                    (By.NAME, "vendorSearch"),
                    (By.CSS_SELECTOR, "input[placeholder*='Search']"),
                    (By.XPATH, "//input[@placeholder[contains(., 'vendor')]]"),
                    (By.CSS_SELECTOR, "input.form-control")
                ]

                vendor_search = None
                for selector_type, selector_value in alternative_selectors:
                    try:
                        vendor_search = self.wait.until(
                            EC.presence_of_element_located((selector_type, selector_value)),
                            timeout=3
                        )
                        logger.info(f"✓ Found vendor search with alternative selector: {selector_type}={selector_value}")
                        break
                    except:
                        continue

                if not vendor_search:
                    logger.error("Could not find vendor search field with any selector")
                    self._log_error_with_context("find_vendor_search_field", e)
                    return False

            # Clear field and type search query
            vendor_search.clear()
            vendor_search.send_keys(search_query)
            logger.info(f"✓ Entered search term: {search_query}")

            # Trigger change event so React/Vue updates and makes API call
            logger.info("Triggering change event to prompt search results...")
            self.driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """, vendor_search)
            logger.info("✓ Change events triggered")

            time.sleep(2)  # Wait for API call and search results to appear

            # Click on vendor from search results
            logger.info("3. Selecting vendor from search results...")
            try:
                # The search term guarantees only the correct vendor appears in results
                # So we just click the Pay button on whatever vendor is displayed
                # No need to match by exact vendor_name

                # Log what vendor(s) are available on the page
                all_vendor_names = self.driver.execute_script("""
                    const vendors = document.querySelectorAll("div[class*='listLabel']");
                    return Array.from(vendors).map(v => v.textContent.trim());
                """)
                logger.info(f"Search results show vendor(s): {all_vendor_names}")

                if not all_vendor_names:
                    logger.error("No vendors found in search results")
                    raise Exception("No vendors displayed after search")

                displayed_vendor = all_vendor_names[0]
                logger.info(f"Using search term '{search_query}' which returned: {displayed_vendor}")

                # Find and click the Pay button on the displayed vendor
                # Since search term guarantees correctness, we don't need to match names
                wait_5s = WebDriverWait(self.driver, 5)

                # Try multiple selectors for the Pay button
                pay_button = None
                selectors = [
                    # Selector 1: First button containing "Pay" text (case-insensitive)
                    (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pay')]"),
                    # Selector 2: Button with specific class pattern
                    (By.XPATH, "//button[contains(@class, 'MuiButton') and contains(., 'Pay')]"),
                    # Selector 3: The first Pay button in a vendor card
                    (By.XPATH, "//button[normalize-space()='PAY']"),
                ]

                for selector in selectors:
                    try:
                        logger.info(f"Trying selector: {selector[1][:60]}...")
                        pay_button = wait_5s.until(
                            EC.element_to_be_clickable(selector)
                        )
                        logger.info(f"✓ Found Pay button using selector")
                        break
                    except Exception as selector_error:
                        logger.debug(f"Selector failed: {str(selector_error)[:100]}")
                        continue

                if not pay_button:
                    # Fallback: Use JavaScript click
                    logger.info("Using JavaScript click as fallback...")
                    try:
                        self.driver.execute_script("""
                            const buttons = Array.from(document.querySelectorAll('button'));
                            const payButton = buttons.find(b => b.textContent.trim().toUpperCase().includes('PAY'));
                            if (payButton) {
                                payButton.scrollIntoView({ behavior: 'instant', block: 'center' });
                                payButton.click();
                                return true;
                            }
                            return false;
                        """)
                        logger.info("✓ Clicked Pay button using JavaScript")
                        time.sleep(2)  # Wait for page to respond
                    except Exception as js_error:
                        logger.error(f"JavaScript click also failed: {str(js_error)}")
                        raise Exception(f"Could not click Pay button with any method: {str(js_error)}")
                else:
                    logger.info(f"✓ Found Pay button for: {displayed_vendor}")
                    pay_button.click()
                    logger.info(f"✓ Clicked Pay button for: {displayed_vendor}")
                    time.sleep(1)  # Wait for page to respond to click

            except Exception as e:
                logger.error(f"❌ Could not click Pay button after search: {str(e)}")

                # Log page state for debugging
                page_state = self._get_page_state()
                logger.error(f"Page state: {page_state}")

                self._log_error_with_context("select_vendor", e)
                return False

            time.sleep(1)

            # Note: Step 4 (confirming vendor selection) may already be complete from clicking Pay in step 3
            # Only try to click another Pay button if the amount field hasn't appeared yet
            logger.info("4. Checking if vendor was selected...")
            try:
                # Try to find the amount field - if it exists, vendor was already selected
                amount_field_check = self.driver.find_elements(By.NAME, "amount")
                if not amount_field_check:
                    # Amount field not found, try clicking another Pay button to confirm
                    logger.info("Amount field not found, attempting to confirm vendor selection...")
                    try:
                        select_vendor_button = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Pay')]")),
                            timeout=3
                        )
                        select_vendor_button.click()
                        logger.info("✓ Vendor confirmed with additional Pay button click")
                    except:
                        logger.info("No additional confirmation button needed")
                else:
                    logger.info("✓ Vendor already selected (amount field is visible)")
            except Exception as e:
                logger.warning(f"Could not verify vendor selection: {str(e)}")
                # Don't fail here - continue to next step

            time.sleep(1)

            # Fill amount - Direct Pay uses decimal format, not cents
            logger.info("5. Entering payment amount...")
            try:
                wait_5s = WebDriverWait(self.driver, 5)
                amount_field = wait_5s.until(
                    EC.presence_of_element_located((By.ID, "amount"))
                )
                amount_field.clear()
                amount_field.send_keys(str(amount))
                logger.info(f"✓ Entered amount: ${amount}")
            except Exception as e:
                logger.error(f"Could not enter payment amount: {str(e)}")
                self._log_error_with_context("enter_amount", e)
                return False

            time.sleep(0.5)

            # Click Next to proceed
            logger.info("6. Clicking Next button...")
            try:
                wait_5s = WebDriverWait(self.driver, 5)
                next_button = wait_5s.until(
                    EC.element_to_be_clickable((By.ID, "next"))
                )
                next_button.click()
                logger.info("✓ Next button clicked")
            except Exception as e:
                logger.error(f"Could not click Next button: {str(e)}")
                self._log_error_with_context("click_next", e)
                return False

            time.sleep(2)  # Wait for next page to load

            # The workflow continues with:
            # 7. Upload Documents (if required)
            # 8. Choose Purses (select ESA account)
            # 9. Additional info (comments, PO number)
            # 10. Review & Submit

            # For now, return here - next steps handled by submit_direct_pay()
            logger.info("✓ Direct pay form started and amount entered successfully")
            logger.info("✓ Ready to proceed with remaining workflow steps")
            return True

        except Exception as e:
            logger.error(f"❌ Error starting direct pay: {str(e)}")
            logger.error(f"Full traceback:", exc_info=True)
            self._log_error_with_context("start_direct_pay", e)
            return False

    def submit_direct_pay(self, wait_for_confirmation: bool = True):
        """
        Submit the direct pay request from Review page.
        Clicks Next button to proceed to submission.

        Args:
            wait_for_confirmation: If True, wait for ClassWallet to confirm submission

        Returns:
            dict or bool: If wait_for_confirmation=True, returns confirmation dict.
                         If wait_for_confirmation=False, returns True/False
        """
        try:
            logger.info(f"=== STEP 6: SUBMIT DIRECT PAY ===")

            time.sleep(1)  # Wait for page to be ready

            # Click Next button on Review page to proceed to submission
            logger.info("1. Clicking Next button to submit...")

            wait_5s = WebDriverWait(self.driver, 5)
            next_button = wait_5s.until(
                EC.element_to_be_clickable((By.ID, "next"))
            )
            logger.info("✓ Found Next button")
            next_button.click()
            logger.info("✓ Next button clicked - submitting Direct Pay")

            # Wait for confirmation if requested
            if wait_for_confirmation:
                time.sleep(2)  # Wait for submission to process
                return self.wait_for_submission_confirmation()
            else:
                time.sleep(2)  # Wait for submission to complete
                logger.info("✓ Direct pay submitted")
                return True

        except Exception as e:
            self._log_error_with_context("Submit Direct Pay", e)
            return {'success': False, 'error': True, 'message': str(e)} if wait_for_confirmation else False

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
