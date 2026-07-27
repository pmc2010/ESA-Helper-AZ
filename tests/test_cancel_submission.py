"""Tests for canceling an in-progress ClassWallet submission"""

import pytest
from unittest.mock import patch, MagicMock
import app.automation as automation_module
from app.automation import (
    SubmissionOrchestrator,
    cancel_active_submission,
    submit_to_classwallet,
)


@pytest.fixture(autouse=True)
def reset_cancellation_state():
    """Make sure no test leaks active-submission state into another test."""
    automation_module._active_orchestrator = None
    automation_module._cancel_requested = False
    yield
    automation_module._active_orchestrator = None
    automation_module._cancel_requested = False


class TestCancelActiveSubmission:
    """Test cancel_active_submission() directly"""

    def test_returns_false_when_nothing_active(self):
        assert cancel_active_submission() is False

    def test_closes_browser_and_returns_true_when_active(self):
        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = MagicMock()
        automation_module._active_orchestrator = orchestrator

        result = cancel_active_submission()

        assert result is True
        orchestrator.automation.close.assert_called_once()
        assert automation_module._cancel_requested is True

    def test_handles_close_raising_gracefully(self):
        """If closing the browser itself errors, cancellation should still report success"""
        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = MagicMock()
        orchestrator.automation.close.side_effect = Exception("driver already gone")
        automation_module._active_orchestrator = orchestrator

        result = cancel_active_submission()

        assert result is True


class TestSubmitToClassWalletLifecycle:
    """Test that submit_to_classwallet() registers/clears the active orchestrator correctly"""

    @patch('app.automation.load_config')
    def test_clears_active_orchestrator_on_early_failure(self, mock_load_config):
        """Credential failure returns before the browser-wait loop - state should still clean up"""
        mock_load_config.return_value = None  # No credentials configured

        result = submit_to_classwallet({'request_type': 'Reimbursement'}, auto_submit=False)

        assert result['success'] is False
        assert result['error_code'] == 'CREDENTIALS_ERROR'
        assert automation_module._active_orchestrator is None

    @patch('app.automation.load_config')
    @patch('app.automation.ClassWalletAutomation')
    def test_mid_step_cancellation_reports_canceled(self, mock_automation_class, mock_load_config):
        """Simulate the browser being closed via cancel_active_submission() while a step is
        mid-flight (the step then fails, as its Selenium call would raise) - the final result
        should be reported as an explicit cancellation, not a generic submission failure."""
        mock_load_config.return_value = {'email': 'test@example.com', 'password': 'test'}

        mock_automation = MagicMock()
        mock_automation.login_to_classwallet.return_value = True
        mock_automation.select_student.return_value = True

        def fake_start_reimbursement():
            # Simulate the user clicking Cancel in ESA Helper mid-automation
            automation_module._cancel_requested = True
            return False

        mock_automation.start_reimbursement.side_effect = fake_start_reimbursement
        mock_automation_class.return_value = mock_automation

        submission_data = {
            'request_type': 'Reimbursement',
            'student': 'Student A',
            'store_name': 'Test Vendor',
            'amount': '100.00',
            'expense_category': 'Test',
            'comment': 'Test',
            'po_number': '20260101_0001',
            'files': {}
        }

        result = submit_to_classwallet(submission_data, auto_submit=False)

        assert result['success'] is False
        assert result.get('canceled') is True
        assert result['error_code'] == 'CANCELED'
        assert automation_module._active_orchestrator is None


class TestCancelSubmissionRoute:
    """Test the POST /api/cancel-submission endpoint"""

    def test_returns_not_canceled_when_nothing_in_progress(self, client):
        response = client.post('/api/cancel-submission')
        data = response.get_json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['canceled'] is False

    @patch('app.automation.cancel_active_submission')
    def test_returns_canceled_when_submission_was_active(self, mock_cancel, client):
        mock_cancel.return_value = True

        response = client.post('/api/cancel-submission')
        data = response.get_json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['canceled'] is True
