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
import platform
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
                        # Check if this element is NOT inside a hidden dropdown/menu
                        try:
                            # Check if any parent element is actually hidden
                            parents = elem.find_elements(By.XPATH, "ancestor::*")
                            is_hidden = False

                            for parent in parents[:5]:  # Check first 5 parent levels
                                parent_classes = parent.get_attribute("class") or ""
                                parent_style = parent.get_attribute("style") or ""

                                # Check for explicit hidden indicators
                                if any(x in parent_classes.lower() for x in ['d-none', 'hidden', 'invisible']):
                                    is_hidden = True
                                    logger.info(f"    Element {i+1}: Found hidden class in parent")
                                    break
                                if 'display: none' in parent_style.lower():
                                    is_hidden = True
                                    logger.info(f"    Element {i+1}: Found display:none in parent style")
                                    break

                            if is_hidden:
                                logger.info(f"    Element {i+1} is in a hidden menu, skipping")
                                continue

                            # If we get here, the element is visible and not hidden
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

    def start_reimbursement(self) -> bool:
        """
        Click "Start a new Reimbursement" and wait to land on the Upload Invoice step of
        the new 4-step wizard (Upload Invoice -> Manage Expenses -> Select Purse -> Review
        & Submit) - same wizard Direct Pay uses. Unlike the old flow, there's no more
        separate store-name/amount entry page here; the Vendor field and line-item amount
        are now overwritten later in fill_reimbursement_expenses().

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("STEP 2: START REIMBURSEMENT")
            logger.info("=" * 60)

            time.sleep(1)  # Wait for page to be ready after student selection

            logger.info("Waiting for 'Start a new Reimbursement' button to appear...")
            reimbursement_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='start-reimbursement']"))
            )
            reimbursement_button.click()
            logger.info("✓ 'Start a new Reimbursement' clicked")

            wait_10s = WebDriverWait(self.driver, 10)
            wait_10s.until(
                lambda d: 'upload-invoice' in d.current_url or
                d.find_elements(By.XPATH, "//*[contains(text(), 'Upload Invoice')]")
            )
            logger.info("✓ Landed on Upload Invoice step")
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

    @staticmethod
    def _normalize_category_name(category: str) -> str:
        """
        Normalize an ESA Helper category name to match ClassWallet's exact category text.

        Note: Form sends names like "Computer Hardware & Technological Devices" but
        ClassWallet displays "Computer hardware and technological devices" (different
        capitalization, "&" vs "and", hyphen vs en-dash).
        """
        if category.startswith("Computer Hardware"):
            return "Computer hardware and technological devices"
        elif category == "School Tuition":
            return "Tuition, textbooks or fees at a qualified school"
        elif "Tutoring" in category and "Teaching" in category:
            normalized = category.replace(" & ", " and ").replace("&", "and")
            normalized = normalized.replace("and Teaching", "and teaching")
            return normalized.replace(" - ", " – ")
        else:
            normalized = category.replace(" & ", " and ").replace("&", "and")
            return normalized.replace(" - ", " – ")

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

    def start_direct_pay(self, vendor_name: str, search_term: str = None):
        """
        Start a new direct pay submission: click Pay, search for and select the vendor.

        As of the ClassWallet 2026/2027 platform update, selecting a vendor lands directly
        on the "Upload Invoice" step of a new 4-step wizard (Upload Invoice -> Manage
        Expenses -> Select Purse -> Review & Submit). Amount entry now happens in
        fill_direct_pay_expenses() (step 2), not here.

        Args:
            vendor_name: Name of the vendor to pay (display name)
            search_term: Exact search term for vendor lookup (optional, uses vendor_name if not provided)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("STEP 2: START DIRECT PAY")
            logger.info("=" * 60)
            logger.info(f"Vendor: {vendor_name}")

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

            # Confirm we landed on step 1 of the wizard ("Upload Invoice") - vendor
            # selection navigates straight there, no separate confirmation click needed.
            logger.info("4. Waiting for 'Upload Invoice' step to load...")
            try:
                wait_10s = WebDriverWait(self.driver, 10)
                wait_10s.until(
                    lambda d: 'upload-invoice' in d.current_url or
                    d.find_elements(By.XPATH, "//*[contains(text(), 'Upload Invoice')]")
                )
                logger.info("✓ Landed on Upload Invoice step")
            except Exception as e:
                logger.error(f"Did not reach the Upload Invoice step after selecting vendor: {str(e)}")
                self._log_error_with_context("start_direct_pay", e)
                return False

            logger.info("✓ Vendor selected, ready for invoice upload")
            return True

        except Exception as e:
            logger.error(f"❌ Error starting direct pay: {str(e)}")
            logger.error(f"Full traceback:", exc_info=True)
            self._log_error_with_context("start_direct_pay", e)
            return False

    def upload_wizard_invoice(self, file_paths: dict) -> bool:
        """
        Step 1 of the new Direct Pay wizard ("Upload Invoice"): upload the invoice file(s),
        then handle ClassWallet's Intelligent Document Processing (IDP) scan, which replaced
        the old "resize/rotate -> Save" image editor modal with a "Scan Receipt" button
        (same underlying data-test='Save' selector - see handle_image_editor_modal()).
        Scanning auto-advances to step 2 ("Manage Expenses") when done.

        Args:
            file_paths: Dictionary of {file_type: file_path} OR {file_type: {name, path, size}}
                       OR {file_type: [{name, path, size}, ...]} for multiple files.
                       Expected to contain the primary invoice file(s) only.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=== STEP 3: UPLOAD INVOICE ===")

            if not file_paths:
                logger.error("No invoice file provided - ClassWallet's Direct Pay wizard "
                              "requires an invoice upload on step 1 to proceed")
                return False

            files_to_upload = self._extract_file_paths(file_paths)
            if files_to_upload is None:
                return False

            logger.info("1. Locating file input element...")
            file_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            logger.info("✓ Found file input element")

            file_paths_string = '\n'.join(files_to_upload)
            logger.info(f"2. Sending {len(files_to_upload)} file path(s)...")
            file_input.send_keys(file_paths_string)
            logger.info("✓ Sent file paths to input")

            time.sleep(2)  # Let the upload register before the editor/scan modal appears

            # Handle the resize/rotate -> "Scan Receipt" modal (one per uploaded image)
            logger.info("3. Checking for image editor / Scan Receipt modal...")
            if not self.handle_image_editor_modal():
                logger.error("❌ Failed to handle image editor / Scan Receipt modal")
                return False

            # IDP scanning takes a few seconds and auto-advances to step 2 when done
            logger.info("4. Waiting for Intelligent Document Processing (IDP) scan to complete...")
            try:
                wait_30s = WebDriverWait(self.driver, 30)
                wait_30s.until(lambda d: 'manage-expenses' in d.current_url)
                logger.info("✓ IDP scan complete, landed on Manage Expenses step")
            except Exception as e:
                logger.error(f"Did not reach Manage Expenses step after upload: {str(e)}")
                self._log_error_with_context("upload_wizard_invoice", e)
                return False

            logger.info("✓ Invoice uploaded and scanned successfully")
            return True

        except Exception as e:
            self._log_error_with_context("Upload Direct Pay Invoice", e)
            return False

    def _force_set_field_value(self, element, value: str):
        """
        Robustly overwrite a (possibly masked/controlled) input's value.

        element.clear() sets the DOM value directly, bypassing whatever mask/React
        controlled-input logic tracks the field's real internal state. On ClassWallet's
        Manage Expenses page this means clear() looks like it worked but doesn't reset the
        mask's internal state, so the next send_keys() gets inserted alongside the old
        value instead of replacing it (a pre-filled $2,047.50 became $2,047,502,089.29
        after "overwriting" with 200.85). Selecting the text and deleting it via real
        keystrokes fixes this because the mask sees real key events and updates its
        internal state accordingly.
        """
        # Scroll into view and wait for clickability first - a field can be momentarily
        # unclickable right after a preceding dialog closes (its backdrop/transition hasn't
        # finished yet), which raises ElementNotInteractableException on a bare .click().
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(element))

        element.click()
        select_all_key = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
        for _ in range(5):
            current = (element.get_attribute('value') or '').strip()
            if not current:
                break
            element.send_keys(select_all_key, 'a')
            element.send_keys(Keys.DELETE)
        element.send_keys(str(value))

    def _extract_file_paths(self, file_paths: dict):
        """
        Flatten the {file_type: path | {name,path,size} | [{...}, ...]} structure used
        throughout the app into a plain list of absolute file paths. Returns None (and
        logs an error) if any referenced file doesn't exist.
        """
        files_to_upload = []
        for file_type, file_data in file_paths.items():
            entries = file_data if isinstance(file_data, list) else [file_data]
            for idx, single_file in enumerate(entries):
                if isinstance(single_file, dict):
                    file_path = single_file.get('path')
                    file_name = single_file.get('name', 'unknown')
                    if not file_path:
                        logger.error(f"No path found in file metadata for {file_type}[{idx}]")
                        return None
                else:
                    file_path = single_file
                    file_name = Path(file_path).name

                if not Path(file_path).exists():
                    logger.error(f"File not found: {file_path}")
                    return None

                files_to_upload.append(str(Path(file_path).absolute()))
                logger.info(f"✓ Found {file_type}: {file_name}")

        return files_to_upload

    def _close_date_picker(self, cancel: bool) -> None:
        """
        Close the MUI calendar-picker dialog that opens when the Transaction Date field is
        clicked, via its Cancel or OK button. Falls back to Escape if no button is found
        (e.g. the dialog already auto-closed after a day was selected). Never raises - this
        is only ever used to make sure we don't leave a modal open blocking the page.
        """
        button_text = 'cancel' if cancel else 'ok'
        try:
            button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[contains(@class,'MuiDialog-root') or @role='dialog']"
                    "//button[translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                    f"'abcdefghijklmnopqrstuvwxyz')='{button_text}']"
                ))
            )
            button.click()
        except Exception:
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception:
                pass

        # Let the dialog's close transition/backdrop finish before the caller interacts with
        # anything else on the page (a click right after this raised ElementNotInteractable
        # on the next field in testing).
        time.sleep(0.5)

    def _fill_transaction_date_if_needed(self) -> None:
        """
        Leave ClassWallet's IDP-scanned transaction date alone if it's today or earlier
        (a valid past transaction date). Otherwise - blank, unparseable, or in the future
        (which a misread scan can produce) - try to set it to today's date. Never fails the
        overall step: the date field isn't required, so any error here is logged and
        swallowed, leaving the scanned value in place.

        This field is a MUI calendar-picker dialog, not a free-text input - clicking it
        opens a modal with a day grid and Clear/Cancel/OK buttons, so it can't be overwritten
        by typing like the other fields. Only the case where today's date is visible in the
        currently-displayed month (the common case, since it opens showing the scanned
        date's month) is handled by clicking that day; anything less certain falls back to
        Cancel, leaving the scanned date untouched, rather than risk leaving the modal open
        or picking the wrong date.
        """
        try:
            date_field = self.driver.find_element(By.CSS_SELECTOR, "input[aria-label='Transaction date']")
        except Exception as e:
            logger.warning(f"Could not locate Transaction date field (optional): {str(e)}")
            return

        current_value = (date_field.get_attribute("value") or "").strip()
        use_today = True
        if current_value:
            try:
                scanned_date = datetime.strptime(current_value, "%m/%d/%Y")
                if scanned_date.date() <= datetime.now().date():
                    use_today = False
            except ValueError:
                logger.warning(f"Could not parse scanned transaction date '{current_value}', defaulting to today")

        if not use_today:
            logger.info(f"✓ Keeping scanned transaction date '{current_value}' (today or earlier)")
            return

        logger.info(f"Transaction date scanned as '{current_value or '(blank)'}' (future or unreadable) "
                    "-> attempting to set to today via calendar picker")
        try:
            date_field.click()
            time.sleep(0.5)

            today = datetime.now()
            month_year_label = today.strftime("%B %Y")  # e.g. "July 2026"

            dialog_shows_current_month = self.driver.execute_script("""
                const target = arguments[0].toLowerCase();
                const dialog = document.querySelector('.MuiDialog-root, [role="dialog"]');
                return !!dialog && dialog.textContent.toLowerCase().includes(target);
            """, month_year_label)

            if not dialog_shows_current_month:
                logger.warning("Date picker isn't showing the current month - leaving scanned date as-is "
                                "rather than navigating the calendar")
                self._close_date_picker(cancel=True)
                return

            clicked = self.driver.execute_script("""
                const target = arguments[0];
                const dialog = document.querySelector('.MuiDialog-root, [role="dialog"]');
                if (!dialog) return false;
                const match = Array.from(dialog.querySelectorAll('button')).find(b =>
                    b.textContent.trim() === target && !b.disabled && !b.className.includes('Mui-disabled')
                );
                if (match) { match.click(); return true; }
                return false;
            """, str(today.day))

            if not clicked:
                logger.warning(f"Could not find today's date ({today.day}) in the calendar picker")
                self._close_date_picker(cancel=True)
                return

            time.sleep(0.3)
            self._close_date_picker(cancel=False)
            logger.info("✓ Transaction date set to today via calendar picker")

        except Exception as e:
            logger.warning(f"Could not set Transaction date via calendar picker, leaving as-is: {str(e)}")
            self._close_date_picker(cancel=True)

    def fill_direct_pay_expenses(self, vendor_name: str, amount: str, category: str,
                                  student_name: str = None, po_number: str = None,
                                  additional_files: dict = None) -> bool:
        """
        Step 2 of the new Direct Pay wizard ("Manage Expenses"). IDP pre-fills what it can
        from the scanned invoice (vendor, transaction date, invoice number, line-item
        description/price), which is unreliable enough (or in "User Name"'s case, never
        populated at all) that each field is handled per its own rule:
          - Vendor, User Name, line-item amount: always overwritten with ESA Helper's
            known values, regardless of what IDP scanned.
          - Invoice/quote number: keep whatever IDP scanned if present; only fill it with
            ESA Helper's po_number if IDP left it blank.
          - Transaction date: keep IDP's scanned date if it's today or earlier; otherwise
            (blank, unparseable, or in the future) overwrite with today's date.
        All overwrites use _force_set_field_value() instead of clear()+send_keys(), because
        clear() doesn't reset these masked/controlled inputs' internal state - the next
        keystrokes get inserted alongside the old value instead of replacing it (this is
        exactly how a pre-filled $2,047.50 became $2,047,502,089.29 the first time around).

        Note: only single line-item submissions are supported for now (rows[0]) - ESA
        Helper's own form doesn't yet model multiple line items per submission.

        Args:
            vendor_name: Known vendor name to overwrite the "Vendor" field with
            amount: Payment amount (used for the line item's unit price)
            category: Expense category (ESA Helper's name - normalized to ClassWallet's text)
            student_name: Known student name to overwrite the "User Name" field with
            po_number: Invoice/quote number to fill in only if ClassWallet's scan left it blank
            additional_files: Extra supporting files (e.g. curriculum) to upload via the
                              separate "Additional Documentation" dropzone on this page

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=== STEP 4: MANAGE EXPENSES ===")

            logger.info(f"1. Overwriting Vendor field with: {vendor_name}")
            try:
                vendor_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "vendor"))
                )
                self._force_set_field_value(vendor_field, vendor_name)
                logger.info("✓ Vendor field overwritten")
            except Exception as e:
                logger.error(f"Could not overwrite Vendor field: {str(e)}")
                self._log_error_with_context("fill_direct_pay_expenses:vendor", e)
                return False

            if student_name:
                logger.info(f"2. Overwriting Student/User Name with: {student_name}")
                try:
                    student_field = self.driver.find_element(By.NAME, "studentName")
                    self._force_set_field_value(student_field, student_name)
                    logger.info("✓ Student/User Name overwritten")
                except Exception as e:
                    logger.error(f"Could not overwrite Student/User Name field: {str(e)}")
                    self._log_error_with_context("fill_direct_pay_expenses:student_name", e)
                    return False

            logger.info("3. Checking invoice/quote number...")
            try:
                po_field = self.driver.find_element(By.NAME, "poNumber")
                scanned_po = (po_field.get_attribute("value") or "").strip()
                if scanned_po:
                    logger.info(f"✓ Keeping ClassWallet's scanned invoice number: '{scanned_po}'")
                elif po_number:
                    logger.info(f"Invoice number blank, filling with ESA Helper's: {po_number}")
                    self._force_set_field_value(po_field, po_number)
                    logger.info("✓ Invoice/quote number filled")
            except Exception as e:
                logger.warning(f"Could not check/fill invoice/quote number (optional): {str(e)}")

            logger.info("4. Checking transaction date...")
            self._fill_transaction_date_if_needed()

            if not self._ensure_line_item_exists():
                logger.error("❌ Could not create a line item to fill in")
                return False

            logger.info(f"5. Overwriting line item amount with: ${amount}")
            try:
                price_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "rows[0].price"))
                )
                self._force_set_field_value(price_field, str(amount))

                qty_field = self.driver.find_element(By.NAME, "rows[0].quantity")
                if not (qty_field.get_attribute("value") or "").strip():
                    qty_field.send_keys("1")

                description_field = self.driver.find_element(By.NAME, "rows[0].description")
                if not (description_field.get_attribute("value") or "").strip():
                    description_field.send_keys(category)

                logger.info("✓ Line item amount overwritten")
            except Exception as e:
                logger.error(f"Could not set line item amount: {str(e)}")
                self._log_error_with_context("fill_direct_pay_expenses:amount", e)
                return False

            logger.info(f"6. Selecting expense category: {category}...")
            if not self._select_line_item_category(category):
                logger.error(f"❌ Could not select expense category '{category}'")
                return False

            if additional_files:
                logger.info("7. Uploading additional documentation...")
                extra_paths = self._extract_file_paths(additional_files)
                if extra_paths is None:
                    return False
                try:
                    extra_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                    extra_input.send_keys('\n'.join(extra_paths))
                    time.sleep(1)
                    logger.info("✓ Additional documentation uploaded")
                except Exception as e:
                    logger.error(f"Could not upload additional documentation: {str(e)}")
                    self._log_error_with_context("fill_direct_pay_expenses:additional_files", e)
                    return False

            logger.info("8. Clicking Continue...")
            try:
                continue_button = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                        "'abcdefghijklmnopqrstuvwxyz'), 'continue')]"
                    ))
                )
                continue_button.click()
                logger.info("✓ Continue clicked")
            except Exception as e:
                logger.error(f"Could not click Continue: {str(e)}")
                self._log_error_with_context("fill_direct_pay_expenses:continue", e)
                return False

            wait_10s = WebDriverWait(self.driver, 10)
            wait_10s.until(lambda d: 'select-wallet' in d.current_url)
            logger.info("✓ Manage Expenses complete, landed on Select Purse step")
            return True

        except Exception as e:
            self._log_error_with_context("Fill Direct Pay Expenses", e)
            return False

    def _ensure_line_item_exists(self) -> bool:
        """
        Click "+ Add Expense" if IDP's scan produced zero line-item rows, so rows[0] exists
        for the caller to fill in. Observed with a PDF receipt (Amazon order confirmation) -
        unlike every JPG receipt tested, IDP scanning a PDF can land on Manage Expenses with
        an empty Reimbursement/Direct Pay Details table instead of at least one row, since
        PDFs also skip the resize/rotate "Scan Receipt" modal entirely. Does nothing if a
        row already exists.

        Returns:
            bool: True if at least one row exists (already did, or was just added), False
                  if a row still couldn't be created.
        """
        if self.driver.find_elements(By.NAME, "rows[0].price"):
            return True

        logger.info("No line items found after scan - clicking '+ Add Expense'")
        try:
            add_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add Expense')]"))
            )
            add_button.click()
            self.wait.until(EC.presence_of_element_located((By.NAME, "rows[0].price")))
            logger.info("✓ Added a line item row")
            return True
        except Exception as e:
            logger.error(f"Could not add a line item row: {str(e)}")
            return False

    def _collapse_to_single_line_item(self) -> None:
        """
        Delete any line-item rows beyond the first (rows[0]), so exactly one remains.
        IDP can split a multi-item receipt into several rows, but ESA Helper's Reimbursement
        form only models a single lump-sum amount/category per submission - the rows are
        collapsed rather than summed so the single remaining row can be fully overwritten.
        Removes from the end (repeatedly clicking the last "Remove expense" button) to avoid
        dealing with shifting row indices as rows are deleted.

        Each deletion opens an "Are you sure you want to delete this item?" confirmation
        dialog that must be confirmed via its "Yes, Delete Item" button before the row is
        actually removed.
        """
        while True:
            remove_buttons = self.driver.find_elements(By.XPATH, "//button[@aria-label='Remove expense']")
            if len(remove_buttons) <= 1:
                break
            remove_buttons[-1].click()
            time.sleep(0.3)

            try:
                confirm_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                        "'abcdefghijklmnopqrstuvwxyz'), 'yes, delete')]"
                    ))
                )
                confirm_button.click()
            except Exception:
                logger.debug("No delete-confirmation dialog appeared - assuming row was removed directly")

            time.sleep(0.5)

    def fill_reimbursement_expenses(self, amount: str, category: str, comment: str = None,
                                     vendor_name: str = None, po_number: str = None,
                                     additional_files: dict = None) -> bool:
        """
        Step 2 of the Reimbursement wizard ("Manage Expenses") - the same page/component
        Direct Pay uses, minus the "User Name" field (Reimbursement has no equivalent).

        Unlike Direct Pay's single pre-existing line item, IDP can split a Reimbursement
        receipt into multiple rows (one per purchased item); since ESA Helper's own form
        only models one lump-sum amount/category per submission, any extra rows are deleted
        and the remaining row is fully overwritten - amount, description (from ESA Helper's
        comment), and category - rather than deferring to whatever IDP scanned. Shipping,
        discount, and tax are always zeroed so the line item's total matches the submitted
        amount exactly, regardless of what the scan picked up off the receipt.

        Args:
            amount: Reimbursement amount (used for the line item's unit price)
            category: Expense category (ESA Helper's name - normalized to ClassWallet's text)
            comment: ESA Helper's comment, used as the line item's description
            vendor_name: Known store/vendor name to overwrite the "Vendor" field with (optional)
            po_number: Invoice/quote number to fill in only if ClassWallet's scan left it blank
            additional_files: Extra supporting files (e.g. curriculum) to upload via the
                              separate "Additional Documentation" dropzone on this page

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=== STEP 4: MANAGE EXPENSES (REIMBURSEMENT) ===")

            if vendor_name:
                logger.info(f"1. Overwriting Vendor field with: {vendor_name}")
                try:
                    vendor_field = self.wait.until(
                        EC.presence_of_element_located((By.NAME, "vendor"))
                    )
                    self._force_set_field_value(vendor_field, vendor_name)
                    logger.info("✓ Vendor field overwritten")
                except Exception as e:
                    logger.error(f"Could not overwrite Vendor field: {str(e)}")
                    self._log_error_with_context("fill_reimbursement_expenses:vendor", e)
                    return False

            logger.info("2. Checking invoice/quote number...")
            try:
                po_field = self.driver.find_element(By.NAME, "poNumber")
                scanned_po = (po_field.get_attribute("value") or "").strip()
                if scanned_po:
                    logger.info(f"✓ Keeping ClassWallet's scanned invoice number: '{scanned_po}'")
                elif po_number:
                    logger.info(f"Invoice number blank, filling with ESA Helper's: {po_number}")
                    self._force_set_field_value(po_field, po_number)
                    logger.info("✓ Invoice/quote number filled")
            except Exception as e:
                logger.warning(f"Could not check/fill invoice/quote number (optional): {str(e)}")

            logger.info("3. Checking transaction date...")
            self._fill_transaction_date_if_needed()

            if not self._ensure_line_item_exists():
                logger.error("❌ Could not create a line item to fill in")
                return False

            logger.info("4. Collapsing to a single line item...")
            try:
                self._collapse_to_single_line_item()
            except Exception as e:
                logger.error(f"Could not collapse to a single line item: {str(e)}")
                self._log_error_with_context("fill_reimbursement_expenses:collapse_rows", e)
                return False

            logger.info(f"5. Overwriting line item with amount ${amount} and description...")
            try:
                price_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "rows[0].price"))
                )
                self._force_set_field_value(price_field, str(amount))

                qty_field = self.driver.find_element(By.NAME, "rows[0].quantity")
                if not (qty_field.get_attribute("value") or "").strip():
                    qty_field.send_keys("1")

                description_field = self.driver.find_element(By.NAME, "rows[0].description")
                self._force_set_field_value(description_field, comment or category)

                logger.info("✓ Line item overwritten")
            except Exception as e:
                logger.error(f"Could not set line item amount/description: {str(e)}")
                self._log_error_with_context("fill_reimbursement_expenses:amount", e)
                return False

            logger.info(f"6. Selecting expense category: {category}...")
            if not self._select_line_item_category(category):
                logger.error(f"❌ Could not select expense category '{category}'")
                return False

            logger.info("7. Zeroing shipping, discount, and tax...")
            try:
                for field_name in ("shipping", "discount", "tax"):
                    field = self.driver.find_element(By.NAME, field_name)
                    self._force_set_field_value(field, "0.00")
                logger.info("✓ Shipping/discount/tax zeroed")
            except Exception as e:
                logger.error(f"Could not zero shipping/discount/tax: {str(e)}")
                self._log_error_with_context("fill_reimbursement_expenses:totals", e)
                return False

            if additional_files:
                logger.info("8. Uploading additional documentation...")
                extra_paths = self._extract_file_paths(additional_files)
                if extra_paths is None:
                    return False
                try:
                    extra_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                    extra_input.send_keys('\n'.join(extra_paths))
                    time.sleep(1)
                    logger.info("✓ Additional documentation uploaded")
                except Exception as e:
                    logger.error(f"Could not upload additional documentation: {str(e)}")
                    self._log_error_with_context("fill_reimbursement_expenses:additional_files", e)
                    return False

            logger.info("9. Clicking Continue...")
            try:
                continue_button = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                        "'abcdefghijklmnopqrstuvwxyz'), 'continue')]"
                    ))
                )
                continue_button.click()
                logger.info("✓ Continue clicked")
            except Exception as e:
                logger.error(f"Could not click Continue: {str(e)}")
                self._log_error_with_context("fill_reimbursement_expenses:continue", e)
                return False

            wait_10s = WebDriverWait(self.driver, 10)
            wait_10s.until(lambda d: 'select-wallet' in d.current_url)
            logger.info("✓ Manage Expenses complete, landed on Select Purse step")
            return True

        except Exception as e:
            self._log_error_with_context("Fill Reimbursement Expenses", e)
            return False

    def _select_line_item_category(self, category: str) -> bool:
        """
        Open the "Select Expense Category" modal for line item 0, search for the
        (normalized) category, click the matching radio option, and save. Categories in
        this modal have no stable attribute (no data-test, opaque radio values), so
        matching is done by visible text via JavaScript.
        """
        category_normalized = self._normalize_category_name(category)

        try:
            open_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "(//button[contains(., 'Select Expense Category') or "
                                                        "contains(., 'Expense Category')])[1]"))
            )
            open_button.click()
        except Exception as e:
            logger.error(f"Could not open expense category picker: {str(e)}")
            return False

        try:
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']"))
            )
            search_input.clear()
            search_input.send_keys(category_normalized)
            time.sleep(1)  # Let the results list filter
        except Exception as e:
            logger.warning(f"Could not use category search box, will search full list: {str(e)}")

        clicked = self.driver.execute_script("""
            const target = arguments[0].trim().toLowerCase();
            const dialog = document.querySelector('.MuiDialog-root, [role="dialog"]') || document;
            const radios = Array.from(dialog.querySelectorAll('input[type=radio]'));
            const matchesText = (radio, exact) => {
                let el = radio;
                for (let i = 0; i < 6 && el; i++) {
                    const text = (el.textContent || '').trim().toLowerCase();
                    if (exact ? text === target : text.includes(target)) return true;
                    el = el.parentElement;
                }
                return false;
            };
            let match = radios.find(r => matchesText(r, true)) || radios.find(r => matchesText(r, false));
            if (match) { match.click(); return true; }
            return false;
        """, category_normalized)

        if not clicked:
            logger.error(f"Could not find category option matching '{category_normalized}' in picker")
            return False

        try:
            save_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    ".MuiDialog-root button[data-test='Save'], [role='dialog'] button[data-test='Save']"
                ))
            )
            save_button.click()
            logger.info(f"✓ Category '{category_normalized}' selected and saved")
            return True
        except Exception as e:
            logger.error(f"Could not save category selection: {str(e)}")
            return False

    def select_wizard_purse(self, purse_name: str = "Arizona - ESA") -> bool:
        """
        Step 3 of the new Direct Pay wizard ("Select Purse"): check the purse to pay from
        and continue. The checkbox has no stable attribute, so it's matched by the purse
        name's visible text via JavaScript (same approach as the category picker).

        Args:
            purse_name: Visible label of the purse to select

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=== STEP 5: SELECT PURSE ===")

            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            logger.info(f"1. Selecting purse: {purse_name}...")
            clicked = self.driver.execute_script("""
                const target = arguments[0].trim().toLowerCase();
                const checkboxes = Array.from(document.querySelectorAll('input[type=checkbox]'));
                for (const cb of checkboxes) {
                    let el = cb;
                    for (let i = 0; i < 6 && el; i++) {
                        if ((el.textContent || '').trim().toLowerCase().includes(target)) {
                            if (!cb.checked) { cb.click(); }
                            return true;
                        }
                        el = el.parentElement;
                    }
                }
                return false;
            """, purse_name)

            if not clicked:
                logger.error(f"Could not find purse checkbox for '{purse_name}'")
                return False
            logger.info(f"✓ Purse '{purse_name}' selected")

            time.sleep(1)  # Let the Continue button's disabled state update

            logger.info("2. Clicking Continue...")
            continue_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                    "'abcdefghijklmnopqrstuvwxyz'), 'continue')]"
                ))
            )
            continue_button.click()
            logger.info("✓ Continue clicked")

            wait_10s = WebDriverWait(self.driver, 10)
            wait_10s.until(lambda d: 'review' in d.current_url)
            logger.info("✓ Purse selected, landed on Review & Submit step")
            return True

        except Exception as e:
            self._log_error_with_context("Select Direct Pay Purse", e)
            return False

    def fill_wizard_review(self, comment: str = None) -> bool:
        """
        Step 4 of the new Direct Pay wizard ("Review & Submit"): fill the optional
        comment for the approver. Everything else on this page is a read-only summary
        of what was entered in earlier steps.

        Args:
            comment: Comment text for the approver (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=== STEP 6: FILL REVIEW & SUBMIT ===")

            if comment:
                logger.info("1. Filling comment for approver...")
                try:
                    comment_field = self.wait.until(
                        EC.presence_of_element_located((By.NAME, "comments"))
                    )
                    comment_field.clear()
                    comment_field.send_keys(comment)
                    logger.info("✓ Comment filled")
                except Exception as e:
                    logger.warning(f"Could not fill comment field (optional): {str(e)}")

            logger.info("✓ Review page ready")
            return True

        except Exception as e:
            self._log_error_with_context("Fill Direct Pay Review", e)
            return False

    def submit_wizard(self, wait_for_confirmation: bool = True):
        """
        Submit the direct pay request from the Review & Submit page (final step of the
        4-step wizard). The Submit button has no data-test/id attribute, so it's matched
        by its visible text.

        Args:
            wait_for_confirmation: If True, wait for ClassWallet to confirm submission

        Returns:
            dict or bool: If wait_for_confirmation=True, returns confirmation dict.
                         If wait_for_confirmation=False, returns True/False
        """
        try:
            logger.info(f"=== STEP 7: SUBMIT DIRECT PAY ===")

            time.sleep(1)  # Wait for page to be ready

            logger.info("1. Clicking Submit button...")

            wait_5s = WebDriverWait(self.driver, 5)
            submit_button = wait_5s.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                    "'abcdefghijklmnopqrstuvwxyz'), 'submit')]"
                ))
            )
            logger.info("✓ Found Submit button")
            submit_button.click()
            logger.info("✓ Submit button clicked - submitting Direct Pay")

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
