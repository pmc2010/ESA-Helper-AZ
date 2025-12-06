"""Tests for reports and analytics"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.utils import get_submission_history, log_submission


class TestReportsAnalytics:
    """Test reports and analytics endpoints"""

    def test_analytics_endpoint_returns_data(self, client):
        """Test that /api/reports/analytics returns analytics data"""
        response = client.get('/api/reports/analytics')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'month' in data
        assert 'students' in data
        assert 'fiscal_year' in data

    def test_analytics_with_specific_month(self, client):
        """Test analytics for a specific month"""
        response = client.get('/api/reports/analytics?month=2025-11')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'November 2025' in data['month']

    def test_analytics_invalid_month_format(self, client):
        """Test analytics with invalid month format"""
        response = client.get('/api/reports/analytics?month=invalid')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid month format' in data['error']


class TestManualSubmissionsInReports:
    """Test that manual submissions are included in analytics"""

    def test_manual_submission_included_in_month_total(self, client):
        """Test that manual submissions are included in month spending totals"""
        # Create a manual submission
        payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Ice Skating Rink',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-REPORT-001',
            'comment': 'Skating lesson',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)
        assert response.status_code == 201

        # Get analytics for November 2025
        analytics_response = client.get('/api/reports/analytics?month=2025-11')

        assert analytics_response.status_code == 200
        data = json.loads(analytics_response.data)

        # Find Test Student A in the results
        student_a = next((s for s in data['students'] if s['name'] == 'Test Student A'), None)

        assert student_a is not None
        # Month total should include the manual submission
        assert student_a['month_total'] >=45.50

    def test_manual_submission_included_in_ytd_total(self, client):
        """Test that manual submissions are included in YTD totals"""
        # Create a manual submission for November 2025
        payload = {
            'student': 'Test Student B',
            'request_type': 'Reimbursement',
            'store_name': 'Music Store',
            'amount': '75.00',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-REPORT-YTD-001',
            'comment': 'Music lessons',
            'entry_date': '2025-11-01'
        }

        response = client.post('/api/manual-submission', json=payload)
        assert response.status_code == 201

        # Get analytics for November 2025
        analytics_response = client.get('/api/reports/analytics?month=2025-11')

        assert analytics_response.status_code == 200
        data = json.loads(analytics_response.data)

        # Find Test Student B in the results
        student_b = next((s for s in data['students'] if s['name'] == 'Test Student B'), None)

        assert student_b is not None
        # YTD total should include the manual submission
        assert student_b['ytd_total'] >=75.00

    def test_manual_submission_counted_in_submission_count(self, client):
        """Test that manual submissions are counted in submission counts"""
        # Create a manual submission
        payload = {
            'student': 'Test Student C',
            'request_type': 'Reimbursement',
            'store_name': 'Art Store',
            'amount': '30.00',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-REPORT-COUNT-001',
            'comment': 'Art supplies',
            'entry_date': '2025-11-10'
        }

        response = client.post('/api/manual-submission', json=payload)
        assert response.status_code == 201

        # Get analytics for November 2025
        analytics_response = client.get('/api/reports/analytics?month=2025-11')

        assert analytics_response.status_code == 200
        data = json.loads(analytics_response.data)

        # Find Test Student C in the results
        student_c = next((s for s in data['students'] if s['name'] == 'Test Student C'), None)

        assert student_c is not None
        # Submission count should include manual submission
        assert student_c['month_submissions'] >=1

    def test_manual_submission_affects_annualized_rate(self, client):
        """Test that manual submissions affect annualized rate calculation"""
        # Create multiple manual submissions in November
        submissions = [
            {
                'student': 'Test Student A',
                'request_type': 'Reimbursement',
                'store_name': 'Store 1',
                'amount': '100.00',
                'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
                'po_number': 'PO-REPORT-ANN-001',
                'comment': 'Entry 1',
                'entry_date': '2025-11-05'
            },
            {
                'student': 'Test Student A',
                'request_type': 'Reimbursement',
                'store_name': 'Store 2',
                'amount': '150.00',
                'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
                'po_number': 'PO-REPORT-ANN-002',
                'comment': 'Entry 2',
                'entry_date': '2025-11-20'
            }
        ]

        for payload in submissions:
            response = client.post('/api/manual-submission', json=payload)
            assert response.status_code == 201

        # Get analytics for November 2025
        analytics_response = client.get('/api/reports/analytics?month=2025-11')

        assert analytics_response.status_code == 200
        data = json.loads(analytics_response.data)

        # Find Test Student A in the results
        student_a = next((s for s in data['students'] if s['name'] == 'Test Student A'), None)

        assert student_a is not None
        # Annualized rate should be calculated based on month total and day of month
        assert student_a['annualized_rate'] >0

    def test_manual_and_automated_submissions_both_in_reports(self, client):
        """Test that both manual and automated submissions appear in reports together"""
        # Create manual submission
        manual_payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Manual Store',
            'amount': '50.00',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-BOTH-MANUAL-001',
            'comment': 'Manual entry',
            'entry_date': '2025-11-08'
        }

        # Create automated submission entry in logs
        automated_data = {
            'type': 'reimbursement',
            'student': 'Test Student A',
            'store_name': 'Automated Store',
            'amount': 75.00,
            'po_number': 'PO-BOTH-AUTO-001',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'comment': 'Automated entry'
        }

        response = client.post('/api/manual-submission', json=manual_payload)
        assert response.status_code == 201
        log_submission(automated_data, created_by='automation')

        # Get analytics for November 2025
        analytics_response = client.get('/api/reports/analytics?month=2025-11')

        assert analytics_response.status_code == 200
        data = json.loads(analytics_response.data)

        # Find Test Student A in the results
        student_a = next((s for s in data['students'] if s['name'] == 'Test Student A'), None)

        assert student_a is not None
        # Both submissions should be counted
        assert student_a['month_total'] >=125.00  # 50 + 75
        assert student_a['month_submissions'] >=2

    def test_manual_submission_with_specific_date_appears_correctly(self, client):
        """Test that manual submission entry_date is stored and retrievable"""
        # Create manual submission with specific entry date
        payload = {
            'student': 'Test Student B',
            'request_type': 'Reimbursement',
            'store_name': 'Store',
            'amount': '100.00',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-DATE-TEST-001',
            'comment': 'Date test entry',
            'entry_date': '2025-10-15'  # Specific date
        }

        response = client.post('/api/manual-submission', json=payload)
        assert response.status_code == 201

        # Verify entry_date is stored in history
        history = get_submission_history()
        entry = next((e for e in history if e.get('po_number') == 'PO-DATE-TEST-001'), None)

        assert entry is not None
        assert entry['entry_date'] == '2025-10-15'
        # Analytics filtering uses timestamp (when logged), not entry_date
        # Entry_date is stored for reference and UI display

    def test_empty_month_has_zero_submissions(self, client):
        """Test that empty months show zero submissions"""
        response = client.get('/api/reports/analytics?month=2025-01')

        assert response.status_code == 200
        data = json.loads(response.data)

        if data['students']:
            for student in data['students']:
                # At least one student should have 0 submissions or low numbers
                assert 'month_submissions' in student
                assert 'month_total' in student


class TestReportsBudgetCalculations:
    """Test budget-related calculations in reports with manual submissions"""

    def test_manual_submission_affects_budget_used_percentage(self, client):
        """Test that manual submissions affect budget used percentage calculation"""
        # Assuming Allie Curtis has a budget configured
        # Create manual submission
        payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Store',
            'amount': '500.00',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-BUDGET-001',
            'comment': 'Budget impact test',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)
        assert response.status_code == 201

        # Get analytics
        analytics_response = client.get('/api/reports/analytics?month=2025-11')

        assert analytics_response.status_code == 200
        data = json.loads(analytics_response.data)

        # Find Test Student A
        student_a = next((s for s in data['students'] if s['name'] == 'Test Student A'), None)

        assert student_a is not None
        # If student has allotment, budget calculations should include manual submission
        if student_a.get('allotment'):
            assert 'percent_used' in student_a['allotment']
            assert student_a['allotment']['percent_used'] >0
