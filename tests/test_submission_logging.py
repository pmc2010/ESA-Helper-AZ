"""Tests for submission history logging"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.utils import log_submission, get_submission_history


class TestSubmissionLogging:
    """Test submission logging functionality"""

    def test_log_submission_creates_entry(self):
        """Test that log_submission creates a submission entry"""
        submission_data = {
            'type': 'direct_pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'amount': '200.85',
            'po_number': '20251111_1234',
            'expense_category': 'Tutoring & Teaching Services',
            'comment': 'Horse riding lessons'
        }

        log_file = log_submission(submission_data, created_by='test')

        assert log_file.exists()
        with open(log_file, 'r') as f:
            logged = json.load(f)
            assert logged['type'] == 'direct_pay'
            assert logged['student'] == 'Student A'
            assert logged['vendor_name'] == 'Hayden Acres'
            assert logged['amount'] == '200.85'

    def test_log_submission_includes_category_and_comment(self):
        """Test that category and comment are included in logged submission"""
        submission_data = {
            'type': 'reimbursement',
            'student': 'Student B',
            'store_name': 'Test Store',
            'amount': '150.00',
            'po_number': '20251111_5678',
            'expense_category': 'Computer Hardware',
            'comment': 'Test comment'
        }

        log_file = log_submission(submission_data, created_by='test')

        with open(log_file, 'r') as f:
            logged = json.load(f)
            assert logged['expense_category'] == 'Computer Hardware'
            assert logged['comment'] == 'Test comment'

    def test_log_submission_updates_history(self):
        """Test that log_submission updates the master history file"""
        submission_data = {
            'type': 'direct_pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'amount': '200.85',
            'po_number': '20251111_1234',
            'expense_category': 'Tutoring & Teaching Services',
            'comment': 'Horse riding'
        }

        log_submission(submission_data, created_by='test')

        # Get history and verify entry was added
        history = get_submission_history()
        assert len(history) > 0

        # Find our entry
        found = False
        for entry in history:
            if entry.get('po_number') == '20251111_1234':
                found = True
                assert entry['type'] == 'direct_pay'
                assert entry['expense_category'] == 'Tutoring & Teaching Services'
                assert entry['comment'] == 'Horse riding'
                break

        assert found, "Submission not found in history"

    def test_log_submission_with_optional_fields(self):
        """Test logging submission with optional fields"""
        submission_data = {
            'type': 'direct_pay',
            'student': 'Student A',
            'vendor_name': 'Test Vendor',
            'amount': '100.00',
            'po_number': '20251111_9999',
            'expense_category': 'Test Category',
            'comment': None  # Optional, can be None
        }

        log_file = log_submission(submission_data, created_by='test')

        with open(log_file, 'r') as f:
            logged = json.load(f)
            assert logged['comment'] is None

    def test_get_submission_history_returns_all_submissions(self):
        """Test get_submission_history returns all submissions"""
        # Create multiple submissions
        submissions = [
            {
                'type': 'direct_pay',
                'student': 'Student A',
                'vendor_name': 'Vendor 1',
                'amount': '100.00',
                'po_number': '20251111_0001',
                'expense_category': 'Category 1',
                'comment': 'Comment 1'
            },
            {
                'type': 'reimbursement',
                'student': 'Student B',
                'store_name': 'Store 2',
                'amount': '200.00',
                'po_number': '20251111_0002',
                'expense_category': 'Category 2',
                'comment': 'Comment 2'
            }
        ]

        for submission in submissions:
            log_submission(submission, created_by='test')

        history = get_submission_history()
        assert len(history) >= 2

    def test_get_submission_history_sorts_by_date_descending(self):
        """Test that submission history is sorted newest first"""
        # Log submissions with different timestamps
        submissions = [
            {
                'type': 'direct_pay',
                'student': 'Student A',
                'vendor_name': 'Vendor 1',
                'amount': '100.00',
                'po_number': '20251111_first',
                'expense_category': 'Test',
                'comment': 'First'
            }
        ]

        for submission in submissions:
            log_submission(submission, created_by='test')

        history = get_submission_history()

        # Verify list is sorted (most recent first)
        if len(history) > 1:
            for i in range(len(history) - 1):
                assert history[i]['logged_at'] >= history[i + 1]['logged_at']

    def test_submission_history_includes_required_fields(self):
        """Test that submission history entries include all required fields"""
        submission_data = {
            'type': 'direct_pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'amount': '200.85',
            'po_number': '20251111_1234',
            'expense_category': 'Tutoring & Teaching Services',
            'comment': 'Horse riding'
        }

        log_submission(submission_data, created_by='test')
        history = get_submission_history()

        # Get the most recent entry
        entry = history[0]

        # Check required fields
        assert 'logged_at' in entry
        assert 'timestamp' in entry
        assert 'type' in entry
        assert 'student' in entry
        assert 'amount' in entry
        assert 'po_number' in entry

    def test_direct_pay_submission_logging(self):
        """Test Direct Pay specific submission logging"""
        submission_data = {
            'type': 'direct_pay',
            'student': 'Student A',
            'vendor_name': 'Hayden Acres',
            'amount': '200.85',
            'po_number': '20251111_1234',
            'expense_category': 'Tutoring & Teaching Services',
            'comment': 'Horse riding lessons'
        }

        log_file = log_submission(submission_data, created_by='test')

        with open(log_file, 'r') as f:
            logged = json.load(f)
            assert logged['type'] == 'direct_pay'
            assert logged['vendor_name'] == 'Hayden Acres'
            assert logged['expense_category'] == 'Tutoring & Teaching Services'
            assert logged['comment'] == 'Horse riding lessons'

    def test_reimbursement_submission_logging(self):
        """Test Reimbursement specific submission logging"""
        submission_data = {
            'type': 'reimbursement',
            'student': 'Student B',
            'store_name': 'Test Store',
            'amount': '150.00',
            'po_number': '20251111_5678',
            'expense_category': 'Computer Hardware',
            'comment': 'Computer software purchase'
        }

        log_file = log_submission(submission_data, created_by='test')

        with open(log_file, 'r') as f:
            logged = json.load(f)
            assert logged['type'] == 'reimbursement'
            assert logged['store_name'] == 'Test Store'
            assert logged['expense_category'] == 'Computer Hardware'
            assert logged['comment'] == 'Computer software purchase'

    def test_submission_logging_handles_missing_optional_fields(self):
        """Test that logging handles missing optional fields gracefully"""
        submission_data = {
            'type': 'direct_pay',
            'student': 'Student A',
            'vendor_name': 'Test Vendor',
            'amount': '100.00',
            'po_number': '20251111_9999'
            # expense_category and comment are missing
        }

        # Should not raise an exception
        log_file = log_submission(submission_data, created_by='test')
        assert log_file.exists()

        with open(log_file, 'r') as f:
            logged = json.load(f)
            # Fields should be present but may be None or missing
            assert logged['type'] == 'direct_pay'
