"""
Automation Orchestration Module

Coordinates the full workflow: loading credentials, logging in, and submitting forms.
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, Optional
from app.classwallet import ClassWalletAutomation
from app.utils import load_config, log_submission

logger = logging.getLogger(__name__)


class SubmissionOrchestrator:
    """Orchestrates the full ESA submission workflow"""

    def __init__(self):
        """Initialize orchestrator"""
        self.automation = None
        self.config = None
        self.last_error = None  # Track last error message for display

    def load_credentials(self) -> bool:
        """
        Load credentials from config file

        Returns:
            bool: True if credentials loaded, False if not configured
        """
        try:
            self.config = load_config()
            if not self.config:
                self.last_error = "ClassWallet credentials not configured. Please configure them in Settings → ESA Credentials."
                logger.error("Credentials not configured")
                return False

            logger.info("Credentials loaded successfully")
            return True

        except Exception as e:
            self.last_error = f"Failed to load credentials: {str(e)}"
            logger.error(f"Error loading credentials: {str(e)}")
            return False

    def initialize_automation(self, headless: bool = False) -> bool:
        """
        Initialize ClassWallet automation with loaded credentials

        Args:
            headless: Run browser in headless mode

        Returns:
            bool: True if initialized, False otherwise
        """
        try:
            if not self.config:
                self.last_error = "Credentials not loaded. Please configure ClassWallet credentials first."
                logger.error("Credentials not loaded")
                return False

            self.automation = ClassWalletAutomation(
                email=self.config.get('email'),
                password=self.config.get('password'),
                headless=headless
            )

            logger.info("Automation initialized")
            return True

        except Exception as e:
            self.last_error = f"Failed to initialize browser automation: {str(e)}"
            logger.error(f"Error initializing automation: {str(e)}")
            return False

    def login(self) -> bool:
        """
        Login to ClassWallet

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            if not self.automation:
                self.last_error = "Browser automation not initialized. Please try again."
                logger.error("Automation not initialized")
                return False

            if not self.automation.login_to_classwallet():
                self.last_error = "Failed to login to ClassWallet. Please check your email and password in Settings → ESA Credentials."
                return False

            return True

        except Exception as e:
            self.last_error = f"Login error: {str(e)}"
            logger.error(f"Error logging in: {str(e)}")
            return False

    def submit_reimbursement(self, submission_data: Dict, auto_submit: bool = False) -> bool:
        """
        Submit reimbursement request

        Args:
            submission_data: Dictionary containing:
                - student: Student name
                - store_name: Store/instructor name
                - amount: Reimbursement amount
                - expense_category: Expense category
                - po_number: Purchase order number
                - comment: Comment text
                - files: Dictionary of {file_type: file_path}
            auto_submit: If True, automatically submit without review. If False, stop before final submit.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.automation:
                self.last_error = "Automation not initialized. Please try again."
                logger.error("Automation not initialized")
                return False

            student = submission_data.get('student')
            store_name = submission_data.get('store_name')
            amount = submission_data.get('amount')
            expense_category = submission_data.get('expense_category')
            po_number = submission_data.get('po_number')
            comment = submission_data.get('comment')
            files = submission_data.get('files', {})

            logger.info(f"Starting reimbursement submission for {student} (auto_submit={auto_submit})")

            # Step 1: Select student
            if not self.automation.select_student(student):
                self.last_error = f"Could not select student '{student}' in ClassWallet. Please verify the student exists in ClassWallet."
                return False

            # Step 2: Start reimbursement
            if not self.automation.start_reimbursement(store_name, amount):
                self.last_error = f"Could not start reimbursement for '{store_name}'. The ClassWallet interface may have changed. Check the logs for details."
                return False

            # Step 3: Upload files
            if not self.automation.upload_files(files):
                self.last_error = "Failed to upload files to ClassWallet. Check file format, size, and format. The interface may have changed."
                return False

            # Step 4: Select expense category
            if not self.automation.select_expense_category(expense_category):
                self.last_error = f"Could not select expense category '{expense_category}'. Please verify the category is available in ClassWallet."
                return False

            # Step 5: Fill PO and comment
            if not self.automation.fill_po_and_comment(po_number, comment, auto_submit=auto_submit):
                self.last_error = "Failed to fill purchase order number or comment. The ClassWallet interface may have changed."
                return False

            # Step 6: Submit (only if auto_submit is True)
            if auto_submit:
                if not self.automation.submit_reimbursement():
                    self.last_error = "Failed to submit reimbursement. Please review the form in ClassWallet and submit manually."
                    return False
                logger.info("Reimbursement auto-submitted")
            else:
                logger.info("Auto-submit disabled. Stopped before final submit for manual review.")

            # Log submission
            log_submission({
                'type': 'reimbursement',
                'student': student,
                'store_name': store_name,
                'amount': amount,
                'po_number': po_number,
                'expense_category': submission_data.get('category'),
                'comment': submission_data.get('comment')
            })

            logger.info("Reimbursement workflow completed successfully")
            return True

        except Exception as e:
            self.last_error = f"Unexpected error: {str(e)}"
            logger.error(f"Error submitting reimbursement: {str(e)}")
            return False

    def submit_direct_pay(self, submission_data: Dict, auto_submit: bool = False) -> bool:
        """
        Submit direct pay request

        Args:
            submission_data: Dictionary containing:
                - student: Student name
                - store_name: Vendor name
                - amount: Payment amount
                - expense_category: Expense category
                - po_number: Purchase order number
                - comment: Comment text
                - files: Dictionary of {file_type: file_path}
                - classwallet_search_term: (optional) Exact search term for vendor lookup
            auto_submit: If True, automatically submit without review. If False, stop before final submit.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.automation:
                self.last_error = "Automation not initialized. Please try again."
                logger.error("Automation not initialized")
                return False

            student = submission_data.get('student')
            vendor_name = submission_data.get('vendor_name')  # Direct Pay uses vendor_name
            amount = submission_data.get('amount')
            expense_category = submission_data.get('expense_category')
            po_number = submission_data.get('po_number')
            comment = submission_data.get('comment')
            files = submission_data.get('files', {})
            search_term = submission_data.get('classwallet_search_term')  # Get search term if available

            logger.info(f"Starting direct pay submission for {student} (auto_submit={auto_submit})")

            # Step 1: Select student
            if not self.automation.select_student(student):
                self.last_error = f"Could not select student '{student}' in ClassWallet. Please verify the student exists in ClassWallet."
                return False

            # Step 2: Start direct pay (with optional search_term for vendor lookup)
            if not self.automation.start_direct_pay(vendor_name, amount, search_term=search_term):
                self.last_error = f"Could not find vendor '{vendor_name}' in ClassWallet. Check the vendor name and search term in Manage Vendors."
                return False

            # Step 3: Upload files (no payment receipt for direct pay)
            if not self.automation.upload_files(files):
                self.last_error = "Failed to upload files to ClassWallet. Check file format and size. The interface may have changed."
                return False

            # Step 4: Select expense category
            if not self.automation.select_expense_category(expense_category):
                self.last_error = f"Could not select expense category '{expense_category}'. Please verify the category is available in ClassWallet."
                return False

            # Step 5: Fill additional info (comments and invoice/quote number for Direct Pay)
            if not self.automation.fill_direct_pay_additional_info(po_number, comment):
                self.last_error = "Failed to fill invoice number or comment. The ClassWallet interface may have changed."
                return False

            # Step 5B: Proceed to Review page
            if not self.automation.proceed_direct_pay_to_review():
                self.last_error = "Could not proceed to review page. The ClassWallet interface may have changed."
                return False

            # Step 6: Submit (only if auto_submit is True)
            if auto_submit:
                if not self.automation.submit_direct_pay():
                    self.last_error = "Failed to submit direct pay. Please review the form in ClassWallet and submit manually."
                    return False
                logger.info("Direct pay auto-submitted")
            else:
                logger.info("Auto-submit disabled. Stopped at Review page for manual submission.")

            # Log submission
            log_submission({
                'type': 'direct_pay',
                'student': student,
                'vendor_name': vendor_name,
                'amount': amount,
                'po_number': po_number,
                'expense_category': submission_data.get('category'),
                'comment': submission_data.get('comment')
            })

            logger.info("Direct pay workflow completed successfully")
            return True

        except Exception as e:
            self.last_error = f"Unexpected error: {str(e)}"
            logger.error(f"Error submitting direct pay: {str(e)}")
            return False

    def close(self):
        """Close automation and cleanup"""
        if self.automation:
            self.automation.close()
            logger.info("Automation closed")


def submit_to_classwallet(submission_data: Dict, auto_submit: bool = False) -> Dict:
    """
    Main function to submit to ClassWallet

    Args:
        submission_data: Form submission data
        auto_submit: If True, automatically submit without review. If False, stop before final submit.

    Returns:
        dict: Result status and message
    """
    orchestrator = SubmissionOrchestrator()

    try:
        # Load credentials
        if not orchestrator.load_credentials():
            return {
                'success': False,
                'message': orchestrator.last_error or 'Credentials not configured. Please configure your ClassWallet credentials.',
                'error_code': 'CREDENTIALS_ERROR'
            }

        # Initialize automation
        if not orchestrator.initialize_automation(headless=False):
            return {
                'success': False,
                'message': orchestrator.last_error or 'Failed to initialize browser automation',
                'error_code': 'AUTOMATION_ERROR'
            }

        # Login to ClassWallet
        if not orchestrator.login():
            # DISABLED FOR DEBUGGING: orchestrator.close()
            return {
                'success': False,
                'message': orchestrator.last_error or 'Failed to login to ClassWallet',
                'error_code': 'LOGIN_ERROR'
            }

        # Submit based on request type
        request_type = submission_data.get('request_type')
        if request_type == 'Reimbursement':
            success = orchestrator.submit_reimbursement(submission_data, auto_submit=auto_submit)
        elif request_type == 'Direct Pay':
            success = orchestrator.submit_direct_pay(submission_data, auto_submit=auto_submit)
        else:
            # DISABLED FOR DEBUGGING: orchestrator.close()
            return {
                'success': False,
                'message': 'Invalid request type',
                'error_code': 'INVALID_REQUEST'
            }

        # DISABLED FOR DEBUGGING: orchestrator.close()

        # Prepare response based on success
        if success:
            if auto_submit:
                message = 'Submission successful!'
            else:
                message = 'Form complete and ready for review. Please manually confirm the submission in ClassWallet.'
            response = {
                'success': True,
                'message': message,
                'po_number': submission_data.get('po_number'),
                'auto_submitted': auto_submit
            }
        else:
            response = {
                'success': False,
                'message': orchestrator.last_error or 'Submission failed. Check logs for details.',
                'error_code': 'SUBMISSION_ERROR'
            }

        # Keep browser open indefinitely for user review and manual submission
        logger.info("=" * 60)
        logger.info("BROWSER WILL REMAIN OPEN INDEFINITELY")
        logger.info("Close the browser manually when done reviewing")
        logger.info("=" * 60)

        # Keep the process running, but detect if browser is closed
        try:
            while True:
                try:
                    # Check if browser is still alive by trying a simple operation
                    # This will throw an exception if the browser was closed
                    if orchestrator.automation and orchestrator.automation.driver:
                        orchestrator.automation.driver.current_url
                    time.sleep(1)
                except Exception as browser_check_error:
                    # Browser was closed (driver no longer responsive)
                    logger.info(f"Browser closed by user (detected: {type(browser_check_error).__name__})")
                    return response
        except KeyboardInterrupt:
            logger.info("Browser session closed by user (Ctrl+C)")
            return response

    except Exception as e:
        # DISABLED FOR DEBUGGING: orchestrator.close()
        logger.error(f"Error in submit_to_classwallet: {str(e)}")
        logger.info("=" * 60)
        logger.info("BROWSER WILL REMAIN OPEN INDEFINITELY FOR DEBUGGING")
        logger.info("Close the browser manually when done debugging")
        logger.info("=" * 60)

        error_response = {
            'success': False,
            'message': orchestrator.last_error or f'Unexpected error: {str(e)}',
            'error_code': 'UNEXPECTED_ERROR'
        }

        # Keep the process running, but detect if browser is closed
        try:
            while True:
                try:
                    # Check if browser is still alive by trying a simple operation
                    if orchestrator.automation and orchestrator.automation.driver:
                        orchestrator.automation.driver.current_url
                    time.sleep(1)
                except Exception as browser_check_error:
                    # Browser was closed (driver no longer responsive)
                    logger.info(f"Browser closed by user (detected: {type(browser_check_error).__name__})")
                    return error_response
        except KeyboardInterrupt:
            logger.info("Browser session closed by user (Ctrl+C)")
            return error_response
