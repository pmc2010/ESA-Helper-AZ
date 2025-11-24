"""Tests for Direct Pay automation workflow"""

import pytest
import json
from unittest.mock import patch, MagicMock, call
from app.automation import SubmissionOrchestrator


class TestDirectPayWorkflow:
    """Test Direct Pay submission workflow"""

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_submission_basic_flow(self, mock_automation_class):
        """Test basic Direct Pay submission flow"""
        # Setup mock automation
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation

        # Mock all workflow steps as successful
        mock_automation.login.return_value = True
        mock_automation.select_student.return_value = True
        mock_automation.start_direct_pay.return_value = True
        mock_automation.upload_files.return_value = True
        mock_automation.select_expense_category.return_value = True
        mock_automation.fill_direct_pay_additional_info.return_value = True
        mock_automation.proceed_direct_pay_to_review.return_value = True
        mock_automation.submit_direct_pay.return_value = True

        # Create orchestrator and submit
        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'classwallet_search_term': 'hayden acres llc',
            'amount': '200.85',
            'category': 'Tutoring & Teaching Services',
            'comment': 'Horse riding lessons',
            'po_number': '20251111_1234',
            'files': []
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=True)

        assert result is True
        mock_automation.select_student.assert_called_once_with('Student A')
        mock_automation.start_direct_pay.assert_called_once_with('Hayden Acres', '200.85', search_term='hayden acres llc')

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_with_search_term(self, mock_automation_class):
        """Test Direct Pay uses search term from vendor config"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation

        mock_automation.login.return_value = True
        mock_automation.select_student.return_value = True
        mock_automation.start_direct_pay.return_value = True
        mock_automation.upload_files.return_value = True
        mock_automation.select_expense_category.return_value = True
        mock_automation.fill_direct_pay_additional_info.return_value = True
        mock_automation.proceed_direct_pay_to_review.return_value = True
        mock_automation.submit_direct_pay.return_value = True

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Test Vendor',
            'classwallet_search_term': 'custom search term',
            'amount': '150.00',
            'category': 'Test Category',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': []
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=False)

        # Verify search term was passed to start_direct_pay
        mock_automation.start_direct_pay.assert_called_once()
        call_args = mock_automation.start_direct_pay.call_args
        assert call_args[1]['search_term'] == 'custom search term'

        # Should not call submit_direct_pay when auto_submit=False
        mock_automation.submit_direct_pay.assert_not_called()

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
            'category': 'Test',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': []
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
            'category': 'Test',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': []
        }

        result = orchestrator.submit_direct_pay(submission_data)

        assert result is False
        mock_automation.upload_files.assert_not_called()

    @patch('app.automation.log_submission')
    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_logs_submission(self, mock_automation_class, mock_log_submission):
        """Test Direct Pay logs submission details"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation

        mock_automation.login.return_value = True
        mock_automation.select_student.return_value = True
        mock_automation.start_direct_pay.return_value = True
        mock_automation.upload_files.return_value = True
        mock_automation.select_expense_category.return_value = True
        mock_automation.fill_direct_pay_additional_info.return_value = True
        mock_automation.proceed_direct_pay_to_review.return_value = True
        mock_automation.submit_direct_pay.return_value = True

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'classwallet_search_term': 'hayden acres llc',
            'amount': '200.85',
            'category': 'Tutoring & Teaching Services',
            'comment': 'Horse riding',
            'po_number': '20251111_1234',
            'files': []
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

        mock_automation.login.return_value = True
        mock_automation.select_student.return_value = True
        mock_automation.start_direct_pay.return_value = True
        mock_automation.upload_files.return_value = True
        mock_automation.select_expense_category.return_value = True
        mock_automation.fill_direct_pay_additional_info.return_value = True
        mock_automation.proceed_direct_pay_to_review.return_value = True
        # Note: submit_direct_pay should NOT be called

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'classwallet_search_term': 'hayden acres llc',
            'amount': '200.85',
            'category': 'Test',
            'comment': 'Test',
            'po_number': '20251111_1234',
            'files': []
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=False)

        assert result is True
        mock_automation.proceed_direct_pay_to_review.assert_called_once()
        mock_automation.submit_direct_pay.assert_not_called()


class TestDirectPayAdditionalInfo:
    """Test Direct Pay additional info handling"""

    @patch('app.automation.ClassWalletAutomation')
    def test_direct_pay_fills_po_and_comment(self, mock_automation_class):
        """Test that PO number and comment are filled"""
        mock_automation = MagicMock()
        mock_automation_class.return_value = mock_automation

        mock_automation.login.return_value = True
        mock_automation.select_student.return_value = True
        mock_automation.start_direct_pay.return_value = True
        mock_automation.upload_files.return_value = True
        mock_automation.select_expense_category.return_value = True
        mock_automation.fill_direct_pay_additional_info.return_value = True
        mock_automation.proceed_direct_pay_to_review.return_value = True
        mock_automation.submit_direct_pay.return_value = True

        orchestrator = SubmissionOrchestrator()
        orchestrator.automation = mock_automation

        submission_data = {
            'request_type': 'Direct Pay',
            'student': 'Student A',
            'vendor_name': 'Test Vendor',
            'classwallet_search_term': 'test',
            'amount': '150.00',
            'category': 'Test Category',
            'comment': 'Test comment for vendor',
            'po_number': '20251111_5678',
            'files': []
        }

        result = orchestrator.submit_direct_pay(submission_data, auto_submit=True)

        assert result is True
        mock_automation.fill_direct_pay_additional_info.assert_called_once_with(
            '20251111_5678',
            'Test comment for vendor'
        )
