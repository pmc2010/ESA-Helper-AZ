"""Tests for Direct Pay automation workflow"""

import pytest
import json
from unittest.mock import patch, MagicMock, call
from app.automation import SubmissionOrchestrator


def _mock_successful_workflow(mock_automation):
    """Configure a mock automation object to succeed at every Direct Pay wizard step."""
    mock_automation.login.return_value = True
    mock_automation.select_student.return_value = True
    mock_automation.start_direct_pay.return_value = True
    mock_automation.upload_wizard_invoice.return_value = True
    mock_automation.fill_direct_pay_expenses.return_value = True
    mock_automation.select_wizard_purse.return_value = True
    mock_automation.fill_wizard_review.return_value = True
    mock_automation.submit_wizard.return_value = True


class TestDirectPayWorkflow:
    """Test Direct Pay submission workflow"""

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_submission_basic_flow(self, mock_automation_class):
        """Test basic Direct Pay submission flow"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'classwallet_search_term': 'hayden acres llc',
            'amount': '200.85',
            'expense_category': 'Tutoring & Teaching Services',
            'comment': 'Horse riding lessons',
            'po_number': '20251111_1234',
            'files': {}
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=True)

        assert result is True
        mock_automation.select_student.assert_called_once_with('Student A')
        mock_automation.start_direct_pay.assert_called_once_with('Hayden Acres', search_term='hayden acres llc')
        mock_automation.upload_wizard_invoice.assert_called_once_with({})
        mock_automation.fill_direct_pay_expenses.assert_called_once_with(
            'Hayden Acres', '200.85', 'Tutoring & Teaching Services', student_name='Student A',
            po_number='20251111_1234', additional_files={}
        )
        mock_automation.select_wizard_purse.assert_called_once()
        mock_automation.fill_wizard_review.assert_called_once_with('Horse riding lessons')

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_splits_invoice_from_additional_files(self, mock_automation_class):
        """Test that the 'invoice' file type goes to step 1 and everything else to step 2"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'classwallet_search_term': 'hayden acres llc',
            'amount': '200.85',
            'expense_category': 'Curriculum',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': {
                'invoice': {'name': 'invoice.pdf', 'path': '/tmp/invoice.pdf'},
                'curriculum': {'name': 'curriculum.pdf', 'path': '/tmp/curriculum.pdf'}
            }
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=True)

        assert result is True
        mock_automation.upload_wizard_invoice.assert_called_once_with(
            {'invoice': {'name': 'invoice.pdf', 'path': '/tmp/invoice.pdf'}}
        )
        _, kwargs = mock_automation.fill_direct_pay_expenses.call_args
        assert kwargs['additional_files'] == {'curriculum': {'name': 'curriculum.pdf', 'path': '/tmp/curriculum.pdf'}}

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_only_sends_one_file_to_upload_invoice_step(self, mock_automation_class):
        """ClassWallet's Upload Invoice step only accepts a single file - a second invoice
        file must go to the Additional Documentation dropzone (step 2) instead."""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'classwallet_search_term': 'hayden acres llc',
            'amount': '200.85',
            'expense_category': 'Curriculum',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': {
                'invoice': [
                    {'name': 'invoice1.pdf', 'path': '/tmp/invoice1.pdf'},
                    {'name': 'invoice2.pdf', 'path': '/tmp/invoice2.pdf'}
                ]
            }
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=True)

        assert result is True
        mock_automation.upload_wizard_invoice.assert_called_once_with(
            {'invoice': {'name': 'invoice1.pdf', 'path': '/tmp/invoice1.pdf'}}
        )
        _, kwargs = mock_automation.fill_direct_pay_expenses.call_args
        assert kwargs['additional_files'] == {'invoice': [{'name': 'invoice2.pdf', 'path': '/tmp/invoice2.pdf'}]}

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_with_search_term(self, mock_automation_class):
        """Test Direct Pay uses search term from vendor config"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Test Vendor',
            'classwallet_search_term': 'custom search term',
            'amount': '150.00',
            'expense_category': 'Test Category',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': {}
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=False)

        # Verify search term was passed to start_direct_pay
        mock_automation.start_direct_pay.assert_called_once()
        call_args = mock_automation.start_direct_pay.call_args
        assert call_args[1]['search_term'] == 'custom search term'

        # Should not call submit_wizard when auto_submit=False
        mock_automation.submit_wizard.assert_not_called()
        assert result is True

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_login_failure(self, mock_automation_class):
        """Test Direct Pay fails gracefully if login fails"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation

        mock_automation.login.return_value = False

        orchestrator = SubmissionOrchestrator()

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'classwallet_search_term': 'hayden acres llc',
            'amount': '200.85',
            'expense_category': 'Test',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': {}
        }

        # Note: we're not setting orchestrator.automation, so it will be None
        # and the method should fail
        result = orchestrator.submit_direct_pay(submission_data)

        assert result is False

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_vendor_selection_failure(self, mock_automation_class):
        """Test Direct Pay fails gracefully if vendor selection fails"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation

        mock_automation.login.return_value = True
        mock_automation.select_student.return_value = True
        mock_automation.start_direct_pay.return_value = False

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Nonexistent Vendor',
            'classwallet_search_term': 'invalid',
            'amount': '200.85',
            'expense_category': 'Test',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': {}
        }

        result = orchestrator.submit_direct_pay(submission_data)

        assert result is False
        mock_automation.upload_wizard_invoice.assert_not_called()

    @patch('app.automation.log_submission')
    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_logs_submission(self, mock_automation_class, mock_log_submission):
        """Test Direct Pay logs submission details"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'classwallet_search_term': 'hayden acres llc',
            'amount': '200.85',
            'category': 'Tutoring & Teaching Services',
            'expense_category': 'Tutoring & Teaching Services',
            'comment': 'Horse riding',
            'po_number': '20251111_1234',
            'files': {}
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=True)

        assert result is True
        mock_log_submission.assert_called_once()

        # Verify logged data includes category and comment
        logged_data = mock_log_submission.call_args[0][0]
        assert logged_data['type'] == 'direct_pay'
        assert logged_data['student'] == 'Student A'
        assert logged_data['vendor_name'] == 'Hayden Acres'
        assert logged_data['amount'] == '200.85'
        assert logged_data['po_number'] == '20251111_1234'
        assert logged_data['expense_category'] == 'Tutoring & Teaching Services'
        assert logged_data['comment'] == 'Horse riding'

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_without_auto_submit(self, mock_automation_class):
        """Test Direct Pay without auto-submit stops at review page"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)
        # Note: submit_wizard should NOT be called

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'classwallet_search_term': 'hayden acres llc',
            'amount': '200.85',
            'expense_category': 'Test',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': {}
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=False)

        assert result is True
        mock_automation.fill_wizard_review.assert_called_once()
        mock_automation.submit_wizard.assert_not_called()


class TestDirectPayExpensesStep:
    """Test the Manage Expenses step (known-field fill, amount, category, PO number)"""

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_fills_expenses_with_known_student_name(self, mock_automation_class):
        """Test that the already-known student name is passed through to fill_direct_pay_expenses
        so it can override ClassWallet's IDP-scanned (and often blank) 'User Name' field"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation
        _mock_successful_workflow(mock_automation)

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Test Vendor',
            'classwallet_search_term': 'test',
            'amount': '150.00',
            'expense_category': 'Test Category',
            'comment': 'Test comment for vendor',
            'po_number': '20251111_5678',
            'files': {}
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=True)

        assert result is True
        mock_automation.fill_direct_pay_expenses.assert_called_once_with(
            'Test Vendor', '150.00', 'Test Category', student_name='Student A',
            po_number='20251111_5678', additional_files={}
        )
