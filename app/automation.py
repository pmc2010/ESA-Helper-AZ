"""
Automation Orchestration Module

Coordinates the full workflow: loading credentials, logging in, and submitting forms.
"""

import logging
import json
import time
import threading
from pathlib import Path
from typing import Dict, Optional
from app.classwallet import ClassWalletAutomation
from app.utils import load_config, log_submission

logger = logging.getLogger(__name__)

# Tracks the single in-progress submission (if any) so a concurrent "cancel" request can
# reach in and stop it. ESA Helper is single-user/single-browser by design (see CLAUDE.md),
# so one global slot is sufficient - no per-session tracking needed. Requires the Flask app
# to run with threaded=True, since the request handling submit_to_classwallet() blocks for
# the entire automation and can't otherwise receive a second (cancel) request concurrently.
_active_lock = threading.Lock()
_active_orchestrator: Optional['SubmissionOrchestrator'] = None
_cancel_requested = False


def cancel_active_submission() -> bool:
    """
    Cancel the currently in-progress submission, if any, by quitting its browser. The
    Selenium call that was mid-flight in the automation thread will raise an exception as
    a result, which propagates up through the existing per-step error handling and causes
    submit_to_classwallet() to return a 'canceled' result instead of hanging or silently
    treating it as a plain failure.

    Returns:
        bool: True if a submission was actually canceled, False if none was active.
    """
    global _cancel_requested
    with _active_lock:
        orchestrator = _active_orchestrator
        if orchestrator is None:
            return False
        _cancel_requested = True

    try:
        if orchestrator.automation:
            orchestrator.automation.close()
    except Exception as e:
        logger.warning(f"Error closing browser during cancellation: {str(e)}")

    logger.info("Submission cancellation requested - browser closed")
    return True


def _canceled_response() -> Dict:
    return {
        'success': False,
        'message': 'Submission canceled.',
        'error_code': 'CANCELED',
        'canceled': True
    }


def _split_invoice_files(files: Dict, primary_types: tuple) -> tuple:
    """
    Split a submission's files dict into (invoice_files, additional_files) for the new
    ClassWallet wizard. Step 1's "Upload Invoice" dropzone only accepts a single file -
    confirmed live via ClassWallet's own "only 1 file can be submitted" error when more
    than one was sent at once, even though the underlying <input> technically allows
    multiple. So invoice_files always holds at most one file; anything beyond that
    (including extra files of the primary type itself, e.g. two separate receipts for one
    purchase) goes into additional_files instead, uploaded via step 2's "Additional
    Documentation" dropzone, which does support multiple files.

    Args:
        files: The submission's files dict, e.g. {'invoice': [...], 'curriculum': [...]}
        primary_types: Type keys (lowercase) to look for as the primary invoice/receipt,
                       checked in order - the first one present in `files` wins.

    Returns:
        (invoice_files, additional_files) dicts
    """
    if not isinstance(files, dict):
        return {}, {}

    lower_keys = {k.lower(): k for k in files.keys()}
    primary_key = next((lower_keys[t] for t in primary_types if t in lower_keys), None)

    invoice_files = {}
    additional_files = {}
    for file_type, file_data in files.items():
        if file_type == primary_key:
            entries = file_data if isinstance(file_data, list) else [file_data]
            invoice_files[file_type] = entries[0]
            if len(entries) > 1:
                additional_files[file_type] = entries[1:]
        else:
            additional_files[file_type] = file_data

    return invoice_files, additional_files


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
        Submit reimbursement request, using ClassWallet's 2026/2027 4-step wizard
        (Upload Invoice -> Manage Expenses -> Select Purse -> Review & Submit) - the same
        wizard Direct Pay uses, minus the "User Name" field.

        Args:
            submission_data: Dictionary containing:
                - student: Student name
                - store_name: Store/instructor name
                - amount: Reimbursement amount
                - expense_category: Expense category
                - po_number: Purchase order number
                - comment: Comment text
                - files: Dictionary of {file_type: file_path}. The 'invoice' entry (falling
                         back to 'receipt' if no 'invoice' key is present) is uploaded on
                         step 1; any other file types (e.g. curriculum) are uploaded as
                         additional documentation on step 2.
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
            files = submission_data.get('files', {}) or {}

            invoice_files, additional_files = _split_invoice_files(files, primary_types=('invoice', 'receipt'))

            logger.info(f"Starting reimbursement submission for {student} (auto_submit={auto_submit})")

            # Step 1: Select student
            if not self.automation.select_student(student):
                self.last_error = f"Could not select student '{student}' in ClassWallet. Please verify the student exists in ClassWallet."
                return False

            # Step 2: Start reimbursement (lands on Upload Invoice step)
            if not self.automation.start_reimbursement():
                self.last_error = "Could not start a new reimbursement in ClassWallet. The interface may have changed."
                return False

            # Step 3: Upload the invoice/receipt (triggers IDP scan, advances to Manage Expenses)
            if not self.automation.upload_wizard_invoice(invoice_files):
                self.last_error = "Failed to upload the invoice/receipt to ClassWallet. Check file format and size. The interface may have changed."
                return False

            # Step 4: Manage Expenses - collapse to a single line item, overwrite with
            # ESA Helper's amount/category/comment, zero shipping/discount/tax, Continue
            if not self.automation.fill_reimbursement_expenses(
                amount, expense_category, comment=comment, vendor_name=store_name,
                po_number=po_number, additional_files=additional_files
            ):
                self.last_error = f"Could not fill expense details or select category '{expense_category}'. Please verify the category is available in ClassWallet."
                return False

            # Step 5: Select Purse
            if not self.automation.select_wizard_purse():
                self.last_error = "Could not select the purse to pay from. The ClassWallet interface may have changed."
                return False

            # Step 6: Review & Submit - fill approver comment
            if not self.automation.fill_wizard_review(comment):
                self.last_error = "Failed to fill the review page. The ClassWallet interface may have changed."
                return False

            # Step 7: Submit (only if auto_submit is True)
            actually_submitted = False
            if auto_submit:
                submit_result = self.automation.submit_wizard()
                # submit_wizard() returns a confirmation dict (always truthy, even on
                # failure) rather than a plain bool - check its 'success' key rather than
                # just its truthiness, or a real submission failure would be silently
                # treated as success (and logged as such below).
                actually_submitted = (
                    submit_result.get('success', False) if isinstance(submit_result, dict) else bool(submit_result)
                )
                if not actually_submitted:
                    detail = submit_result.get('message') if isinstance(submit_result, dict) else None
                    self.last_error = detail or "Failed to submit reimbursement. Please review the form in ClassWallet and submit manually."
                    return False
                logger.info("Reimbursement auto-submitted")
            else:
                logger.info("Auto-submit disabled. Stopped before final submit for manual review.")

            # Log submission. auto_submitted reflects whether ClassWallet actually
            # confirmed the submission - when auto_submit is off, the automation only
            # fills the form and waits for the browser to close, so we genuinely don't
            # know whether the user submitted it or backed out; don't claim success either way.
            log_submission({
                'type': 'reimbursement',
                'student': student,
                'store_name': store_name,
                'amount': amount,
                'po_number': po_number,
                'expense_category': submission_data.get('category'),
                'comment': submission_data.get('comment'),
                'auto_submitted': actually_submitted
            })

            logger.info("Reimbursement workflow completed successfully")
            return True

        except Exception as e:
            self.last_error = f"Unexpected error: {str(e)}"
            logger.error(f"Error submitting reimbursement: {str(e)}")
            return False

    def submit_direct_pay(self, submission_data: Dict, auto_submit: bool = False) -> bool:
        """
        Submit direct pay request, using ClassWallet's 2026/2027 4-step wizard
        (Upload Invoice -> Manage Expenses -> Select Purse -> Review & Submit).

        Args:
            submission_data: Dictionary containing:
                - student: Student name
                - store_name: Vendor name
                - amount: Payment amount
                - expense_category: Expense category
                - po_number: Purchase order number
                - comment: Comment text
                - files: Dictionary of {file_type: file_path}. The 'invoice' entry is
                         uploaded on step 1; any other file types (e.g. curriculum) are
                         uploaded as additional documentation on step 2.
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
            files = submission_data.get('files', {}) or {}
            search_term = submission_data.get('classwallet_search_term')  # Get search term if available

            invoice_files, additional_files = _split_invoice_files(files, primary_types=('invoice',))

            logger.info(f"Starting direct pay submission for {student} (auto_submit={auto_submit})")

            # Step 1: Select student
            if not self.automation.select_student(student):
                self.last_error = f"Could not select student '{student}' in ClassWallet. Please verify the student exists in ClassWallet."
                return False

            # Step 2: Start direct pay (search + select vendor; lands on Upload Invoice step)
            if not self.automation.start_direct_pay(vendor_name, search_term=search_term):
                self.last_error = f"Could not find vendor '{vendor_name}' in ClassWallet. Check the vendor name and search term in Manage Vendors."
                return False

            # Step 3: Upload the invoice (triggers IDP scan, advances to Manage Expenses)
            if not self.automation.upload_wizard_invoice(invoice_files):
                self.last_error = "Failed to upload the invoice to ClassWallet. Check file format and size. The interface may have changed."
                return False

            # Step 4: Manage Expenses - known-field overrides, line item amount/category, Continue
            if not self.automation.fill_direct_pay_expenses(
                vendor_name, amount, expense_category, student_name=student,
                po_number=po_number, additional_files=additional_files
            ):
                self.last_error = f"Could not fill expense details or select category '{expense_category}'. Please verify the category is available in ClassWallet."
                return False

            # Step 5: Select Purse
            if not self.automation.select_wizard_purse():
                self.last_error = "Could not select the purse to pay from. The ClassWallet interface may have changed."
                return False

            # Step 6: Review & Submit - fill approver comment
            if not self.automation.fill_wizard_review(comment):
                self.last_error = "Failed to fill the review page. The ClassWallet interface may have changed."
                return False

            # Step 7: Submit (only if auto_submit is True)
            actually_submitted = False
            if auto_submit:
                submit_result = self.automation.submit_wizard()
                # submit_wizard() returns a confirmation dict (always truthy, even on
                # failure) rather than a plain bool - check its 'success' key rather than
                # just its truthiness, or a real submission failure would be silently
                # treated as success (and logged as such below).
                actually_submitted = (
                    submit_result.get('success', False) if isinstance(submit_result, dict) else bool(submit_result)
                )
                if not actually_submitted:
                    detail = submit_result.get('message') if isinstance(submit_result, dict) else None
                    self.last_error = detail or "Failed to submit direct pay. Please review the form in ClassWallet and submit manually."
                    return False
                logger.info("Direct pay auto-submitted")
            else:
                logger.info("Auto-submit disabled. Stopped at Review page for manual submission.")

            # Log submission. auto_submitted reflects whether ClassWallet actually
            # confirmed the submission - when auto_submit is off, the automation only
            # fills the form and waits for the browser to close, so we genuinely don't
            # know whether the user submitted it or backed out; don't claim success either way.
            log_submission({
                'type': 'direct_pay',
                'student': student,
                'vendor_name': vendor_name,
                'amount': amount,
                'po_number': po_number,
                'expense_category': submission_data.get('category'),
                'comment': submission_data.get('comment'),
                'auto_submitted': actually_submitted
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


def _wait_for_browser_close(orchestrator: 'SubmissionOrchestrator', response: Dict) -> Dict:
    """
    Block until the automated browser is closed - either by the user, or by
    cancel_active_submission() quitting it - then return the appropriate response
    (overriding with a canceled result if cancellation was requested for this submission).
    """
    global _cancel_requested

    logger.info("=" * 60)
    logger.info("BROWSER WILL REMAIN OPEN INDEFINITELY")
    logger.info("Close the browser manually when done reviewing")
    logger.info("=" * 60)

    try:
        while True:
            try:
                # Check if browser is still alive by trying a simple operation
                # This will throw an exception if the browser was closed
                if orchestrator.automation and orchestrator.automation.driver:
                    orchestrator.automation.driver.current_url
                time.sleep(0.5)
            except Exception as browser_check_error:
                if _cancel_requested:
                    logger.info("Submission canceled by user - browser closed")
                    return _canceled_response()
                logger.info(f"Browser closed by user (detected: {type(browser_check_error).__name__})")
                return response
    except KeyboardInterrupt:
        logger.info("Browser session closed by user (Ctrl+C)")
        return response


def submit_to_classwallet(submission_data: Dict, auto_submit: bool = False) -> Dict:
    """
    Main function to submit to ClassWallet

    Args:
        submission_data: Form submission data
        auto_submit: If True, automatically submit without review. If False, stop before final submit.

    Returns:
        dict: Result status and message
    """
    global _active_orchestrator, _cancel_requested

    orchestrator = SubmissionOrchestrator()
    with _active_lock:
        _active_orchestrator = orchestrator
        _cancel_requested = False

    try:
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

            # If the browser was closed via cancel_active_submission() while one of the
            # steps above was mid-flight, that step will have failed (its Selenium call
            # raised once the driver quit) - report this as an explicit cancellation
            # rather than a generic submission failure.
            if _cancel_requested:
                logger.info("Submission canceled by user - stopped mid-step")
                return _canceled_response()

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
            return _wait_for_browser_close(orchestrator, response)

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

            return _wait_for_browser_close(orchestrator, error_response)
    finally:
        with _active_lock:
            if _active_orchestrator is orchestrator:
                _active_orchestrator = None
