"""Tests for ClassWalletAutomation.upload_wizard_invoice's handling of IDP scan outcomes"""

from unittest.mock import MagicMock, PropertyMock, patch

from selenium.common.exceptions import TimeoutException

from app.classwallet import ClassWalletAutomation

UPLOAD_URL = 'https://app.classwallet.com/#/reimbursements/wizard/1-upload-invoice'
EXPENSES_URL = 'https://app.classwallet.com/#/reimbursements/wizard/2-manage-expenses'
FILES = {'receipt': '/tmp/test_receipt.png'}


def make_automation(driver):
    automation = ClassWalletAutomation.__new__(ClassWalletAutomation)
    automation.driver = driver
    automation.wait = MagicMock()
    automation.handle_image_editor_modal = MagicMock(return_value=True)
    automation._extract_file_paths = MagicMock(return_value=['/tmp/test_receipt.png'])
    automation._log_error_with_context = MagicMock()
    return automation


@patch('app.classwallet.time.sleep')
class TestUploadWizardInvoice:
    def test_successful_scan_does_not_click_manual_process(self, _sleep):
        driver = MagicMock()
        driver.current_url = EXPENSES_URL

        assert make_automation(driver).upload_wizard_invoice(FILES) is True
        driver.find_element.assert_not_called()

    def test_unreadable_receipt_continues_with_manual_process(self, _sleep):
        driver = MagicMock()
        manual_button = MagicMock()
        driver.find_elements.return_value = [manual_button]
        driver.find_element.return_value = manual_button
        # Stay on the upload step until the manual process button has been clicked
        type(driver).current_url = PropertyMock(
            side_effect=lambda: EXPENSES_URL if manual_button.click.called else UPLOAD_URL
        )

        assert make_automation(driver).upload_wizard_invoice(FILES) is True
        manual_button.click.assert_called_once()

    @patch('app.classwallet.WebDriverWait')
    def test_neither_outcome_fails_upload(self, mock_wait, _sleep):
        driver = MagicMock()
        driver.current_url = UPLOAD_URL
        mock_wait.return_value.until.side_effect = TimeoutException()

        automation = make_automation(driver)
        assert automation.upload_wizard_invoice(FILES) is False
        automation._log_error_with_context.assert_called_once()
