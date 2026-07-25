"""Tests for Reimbursement automation workflow (2026/2027 ClassWallet wizard)"""

import pytest
from unittest.mock import patch, MagicMock
from app.automation import SubmissionOrchestrator


def _mock_successful_workflow(mock_automation):
    """Configure a mock automation object to succeed at every Reimbursement wizard step."""
    mock_automation.login.return_value = True
    mock_automation.select_student.return_value = True
    mock_automation.start_reimbursement.return_value = True
    mock_automation.upload_wizard_invoice.return_value = True
    mock_automation.fill_reimbursement_expenses.return_value = True
    mock_automation.select_wizard_purse.return_value = True
    mock_automation.fill_wizard_review.return_value = True
    mock_automation.submit_wizard.return_value = True


class TestReimbursementWorkflow:
    """Test Reimbursement submission workflow"""

    @patch('app.automation.ClassWalletAutomation')
    def test_reimbursement_submission_basic_flow(self, mock_automation_class):
        """Test basic Reimbursement submission flow"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Reimbursement',
            'student': 'Student A',
            'store_name': 'Test Vendor Inc.',
            'amount': '453.62',
            'expense_category': 'Supplemental Materials',
            'comment': 'Curriculum materials',
            'po_number': '20260724_1234',
            'files': {
                'invoice': {'name': 'invoice.jpg', 'path': '/tmp/invoice.jpg'},
                'curriculum': {'name': 'curriculum.pdf', 'path': '/tmp/curriculum.pdf'}
            }
        }

        result = orchestrator.submit_reimbursement(submission_data, auto_submit=True)

        assert result is True
        mock_automation.select_student.assert_called_once_with('Student A')
        mock_automation.start_reimbursement.assert_called_once_with()
        mock_automation.upload_wizard_invoice.assert_called_once_with(
            {'invoice': {'name': 'invoice.jpg', 'path': '/tmp/invoice.jpg'}}
        )
        mock_automation.fill_reimbursement_expenses.assert_called_once_with(
            '453.62', 'Supplemental Materials', comment='Curriculum materials',
            vendor_name='Test Vendor Inc.', po_number='20260724_1234',
            additional_files={'curriculum': {'name': 'curriculum.pdf', 'path': '/tmp/curriculum.pdf'}}
        )
        mock_automation.select_wizard_purse.assert_called_once()
        mock_automation.fill_wizard_review.assert_called_once_with('Curriculum materials')
        mock_automation.submit_wizard.assert_called_once()

    @patch('app.automation.ClassWalletAutomation')
    def test_reimbursement_falls_back_to_receipt_when_no_invoice_file(self, mock_automation_class):
        """Test that 'receipt' is used as the primary (step 1) file when no 'invoice' key exists"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Reimbursement',
            'student': 'Student A',
            'store_name': 'Test Vendor',
            'amount': '100.00',
            'expense_category': 'Tutoring',
            'comment': 'Test',
            'po_number': '20260724_5678',
            'files': {
                'receipt': {'name': 'receipt.jpg', 'path': '/tmp/receipt.jpg'},
                'attestation': {'name': 'attestation.pdf', 'path': '/tmp/attestation.pdf'}
            }
        }

        result = orchestrator.submit_reimbursement(submission_data, auto_submit=False)

        assert result is True
        mock_automation.upload_wizard_invoice.assert_called_once_with(
            {'receipt': {'name': 'receipt.jpg', 'path': '/tmp/receipt.jpg'}}
        )
        _, kwargs = mock_automation.fill_reimbursement_expenses.call_args
        assert kwargs['additional_files'] == {'attestation': {'name': 'attestation.pdf', 'path': '/tmp/attestation.pdf'}}
        mock_automation.submit_wizard.assert_not_called()

    @patch('app.automation.ClassWalletAutomation')
    def test_reimbursement_login_failure(self, mock_automation_class):
        """Test Reimbursement fails gracefully if login fails"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        mock_automation.login.return_value = False

        orchestrator = SubmissionOrchestrator()

        submission_data = {
            'request_type': 'Reimbursement',
            'student': 'Student A',
            'store_name': 'Test Vendor',
            'amount': '100.00',
            'expense_category': 'Test',
            'comment': 'Test',
            'po_number': '20260724_1111',
            'files': {}
        }

        # Note: we're not setting orchestrator.automation, so it will be None
        # and the method should fail
        result = orchestrator.submit_reimbursement(submission_data)

        assert result is False

    @patch('app.automation.ClassWalletAutomation')
    def test_reimbursement_start_failure(self, mock_automation_class):
        """Test Reimbursement fails gracefully if starting a new reimbursement fails"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation

        mock_automation.login.return_value = True
        mock_automation.select_student.return_value = True
        mock_automation.start_reimbursement.return_value = False

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Reimbursement',
            'student': 'Student A',
            'store_name': 'Test Vendor',
            'amount': '100.00',
            'expense_category': 'Test',
            'comment': 'Test',
            'po_number': '20260724_2222',
            'files': {}
        }

        result = orchestrator.submit_reimbursement(submission_data)

        assert result is False
        mock_automation.upload_wizard_invoice.assert_not_called()

    @patch('app.automation.log_submission')
    @patch('app.automation.ClassWalletAutomation')
    def test_reimbursement_logs_submission(self, mock_automation_class, mock_log_submission):
        """Test Reimbursement logs submission details"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Reimbursement',
            'student': 'Student A',
            'store_name': 'Test Vendor',
            'amount': '453.62',
            'category': 'Supplemental Materials',
            'expense_category': 'Supplemental Materials',
            'comment': 'Curriculum materials',
            'po_number': '20260724_3333',
            'files': {}
        }

        result = orchestrator.submit_reimbursement(submission_data, auto_submit=True)

        assert result is True
        mock_log_submission.assert_called_once()

        logged_data = mock_log_submission.call_args[0][0]
        assert logged_data['type'] == 'reimbursement'
        assert logged_data['student'] == 'Student A'
        assert logged_data['store_name'] == 'Test Vendor'
        assert logged_data['amount'] == '453.62'
        assert logged_data['po_number'] == '20260724_3333'
        assert logged_data['expense_category'] == 'Supplemental Materials'
        assert logged_data['comment'] == 'Curriculum materials'

    @patch('app.automation.ClassWalletAutomation')
    def test_reimbursement_without_auto_submit(self, mock_automation_class):
        """Test Reimbursement without auto-submit stops at review page"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Reimbursement',
            'student': 'Student A',
            'store_name': 'Test Vendor',
            'amount': '100.00',
            'expense_category': 'Test',
            'comment': 'Test',
            'po_number': '20260724_4444',
            'files': {}
        }

        result = orchestrator.submit_reimbursement(submission_data, auto_submit=False)

        assert result is True
        mock_automation.fill_wizard_review.assert_called_once()
        mock_automation.submit_wizard.assert_not_called()

    @patch('app.automation.ClassWalletAutomation')
    def test_reimbursement_no_files_uploads_empty_dict(self, mock_automation_class):
        """Test that an empty files dict is handled gracefully (no invoice/receipt provided)"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Reimbursement',
            'student': 'Student A',
            'store_name': 'Test Vendor',
            'amount': '100.00',
            'expense_category': 'Test',
            'comment': 'Test',
            'po_number': '20260724_5555',
            'files': []
        }

        result = orchestrator.submit_reimbursement(submission_data, auto_submit=True)

        assert result is True
        mock_automation.upload_wizard_invoice.assert_called_once_with({})
        _, kwargs = mock_automation.fill_reimbursement_expenses.call_args
        assert kwargs['additional_files'] == {}
