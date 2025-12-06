"""Tests for manual submission feature"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app.utils import get_submission_history, log_submission


class TestManualSubmissionAPI:
    """Test manual submission API endpoints"""

    def test_post_manual_submission_creates_entry(self, client):
        """Test that POST /api/manual-submission creates a manual entry"""
        payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Test Activity Center',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-001',
            'comment': 'Test lesson',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'Manual transaction logged successfully' in data['message']
        assert data['po_number'] == 'PO-2025-001'

    def test_post_manual_submission_reimbursement_requires_store_name(self, client):
        """Test that Reimbursement type requires store_name"""
        payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-002',
            'comment': 'Test',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required fields' in data['message']

    def test_post_manual_submission_direct_pay_requires_vendor_name(self, client):
        """Test that Direct Pay type requires vendor_name"""
        payload = {
            'student': 'Test Student A',
            'request_type': 'Direct Pay',
            'amount': '100.00',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-003',
            'comment': 'Test',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required fields' in data['message']

    def test_post_manual_submission_direct_pay_with_vendor_name(self, client):
        """Test that Direct Pay submission works with vendor_name"""
        payload = {
            'student': 'Test Student B',
            'request_type': 'Direct Pay',
            'vendor_name': 'Test Vendor LLC',
            'amount': '150.00',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-004',
            'comment': 'Test lesson',
            'entry_date': '2025-11-10'
        }

        response = client.post('/api/manual-submission', json=payload)

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True

    def test_post_manual_submission_missing_required_fields(self, client):
        """Test that missing required fields are rejected"""
        payload = {
            'student': 'Test Student A',
            # Missing request_type
            'store_name': 'Test Store',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-005',
            'comment': 'Test',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required fields' in data['message']

    def test_post_manual_submission_invalid_request_type(self, client):
        """Test that invalid request_type is rejected"""
        payload = {
            'student': 'Test Student A',
            'request_type': 'Invalid Type',
            'store_name': 'Test Store',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-006',
            'comment': 'Test',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid request type' in data['message']

    def test_put_manual_submission_updates_entry(self, client):
        """Test that PUT /api/manual-submission/{po_number} updates an entry"""
        # First create an entry
        create_payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Old Store',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-100',
            'comment': 'Original comment',
            'entry_date': '2025-11-15'
        }

        client.post('/api/manual-submission', json=create_payload)

        # Now update it
        update_payload = {
            'store_name': 'New Store',
            'amount': '75.00',
            'comment': 'Updated comment'
        }

        response = client.put('/api/manual-submission/PO-2025-100', json=update_payload)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'updated successfully' in data['message']

    def test_put_manual_submission_preserves_non_editable_fields(self, client):
        """Test that non-editable fields are preserved during update"""
        # Create entry
        create_payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Store',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-101',
            'comment': 'Original',
            'entry_date': '2025-11-15'
        }

        client.post('/api/manual-submission', json=create_payload)

        # Try to update non-editable fields
        update_payload = {
            'amount': '75.00',
            'entry_date': '2025-10-01',  # This should NOT be editable
            'source': 'automated'  # This should NOT be editable
        }

        client.put('/api/manual-submission/PO-2025-101', json=update_payload)

        # Verify the entry was updated with amount but entry_date and source preserved
        history = get_submission_history()
        entry = next((e for e in history if e.get('po_number') == 'PO-2025-101'), None)

        assert entry is not None
        assert entry['amount'] == 75.00
        assert entry['entry_date'] == '2025-11-15'  # Original date preserved
        assert entry['source'] == 'manual'  # Original source preserved

    def test_delete_manual_submission_removes_entry(self, client):
        """Test that DELETE /api/manual-submission/{po_number} deletes an entry"""
        # Create entry
        create_payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Store',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-102',
            'comment': 'To be deleted',
            'entry_date': '2025-11-15'
        }

        client.post('/api/manual-submission', json=create_payload)

        # Verify it exists
        history = get_submission_history()
        exists = any(e.get('po_number') == 'PO-2025-102' for e in history)
        assert exists is True

        # Delete it
        response = client.delete('/api/manual-submission/PO-2025-102')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'deleted successfully' in data['message']

        # Verify it's gone
        history = get_submission_history()
        exists = any(e.get('po_number') == 'PO-2025-102' for e in history)
        assert exists is False

    def test_delete_nonexistent_manual_submission(self, client):
        """Test deleting a non-existent entry returns error"""
        response = client.delete('/api/manual-submission/PO-NONEXISTENT')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False


class TestManualSubmissionLogging:
    """Test manual submission logging"""

    def test_manual_submission_is_logged_correctly(self):
        """Test that manual submission is logged with correct source flag"""
        submission_data = {
            'type': 'manual_entry',
            'source': 'manual',
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Ice Skating Rink',
            'amount': 45.50,
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-200',
            'comment': 'Skating lesson',
            'entry_date': '2025-11-15'
        }

        log_file = log_submission(submission_data, created_by='manual')

        # Verify file exists and contains correct data
        assert log_file.exists()
        with open(log_file, 'r') as f:
            logged = json.load(f)
            assert logged['type'] == 'manual_entry'
            assert logged['source'] == 'manual'
            assert logged['entry_date'] == '2025-11-15'
            assert logged['store_name'] == 'Ice Skating Rink'
            assert logged['amount'] == 45.50

    def test_manual_submission_appears_in_history(self):
        """Test that manual submissions appear in submission history"""
        submission_data = {
            'type': 'manual_entry',
            'source': 'manual',
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Test Store',
            'amount': 50.00,
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-201',
            'comment': 'Test manual entry',
            'entry_date': '2025-11-14'
        }

        log_submission(submission_data, created_by='manual')

        history = get_submission_history()
        entry = next((e for e in history if e.get('po_number') == 'PO-2025-201'), None)

        assert entry is not None
        assert entry['source'] == 'manual'
        assert entry['type'] == 'manual_entry'

    def test_direct_pay_manual_submission_logged_correctly(self):
        """Test that Direct Pay manual submissions are logged with vendor_name"""
        submission_data = {
            'type': 'manual_entry',
            'source': 'manual',
            'student': 'Test Student B',
            'request_type': 'Direct Pay',
            'vendor_name': 'Test Vendor LLC',
            'amount': 150.00,
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-202',
            'comment': 'Horse riding',
            'entry_date': '2025-11-10'
        }

        log_submission(submission_data, created_by='manual')

        history = get_submission_history()
        entry = next((e for e in history if e.get('po_number') == 'PO-2025-202'), None)

        assert entry is not None
        assert entry['vendor_name'] == 'Hayden Acres'
        assert entry['request_type'] == 'Direct Pay'


class TestManualSubmissionFiltering:
    """Test filtering manual submissions in history"""

    def test_manual_submissions_have_source_flag(self, client):
        """Test that manual submissions can be identified by source flag"""
        # Create a manual submission
        payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Test Store',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-FILTER-001',
            'comment': 'Filter test',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)
        assert response.status_code == 201

        # Verify it's in history with source flag
        history = get_submission_history()
        entry = next((e for e in history if e.get('po_number') == 'PO-FILTER-001'), None)

        assert entry is not None
        assert entry['source'] == 'manual'
        assert entry['type'] == 'manual_entry'

    def test_manual_and_automated_submissions_coexist(self, client):
        """Test that manual and automated submissions can coexist in history"""
        # Create manual submission
        manual_payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Manual Store',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-COEXIST-001',
            'comment': 'Manual entry',
            'entry_date': '2025-11-15'
        }

        # Create automated submission entry
        automated_data = {
            'type': 'reimbursement',
            'student': 'Test Student B',
            'store_name': 'Automated Store',
            'amount': 100.00,
            'po_number': 'PO-COEXIST-002',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'comment': 'Automated entry'
        }

        client.post('/api/manual-submission', json=manual_payload)
        log_submission(automated_data, created_by='automation')

        history = get_submission_history()
        manual_entry = next((e for e in history if e.get('po_number') == 'PO-COEXIST-001'), None)
        automated_entry = next((e for e in history if e.get('po_number') == 'PO-COEXIST-002'), None)

        assert manual_entry is not None
        assert manual_entry['source'] == 'manual'
        assert automated_entry is not None
        # Automated entries may or may not have source field, but if present should not be 'manual'
        assert automated_entry.get('source') != 'manual'


class TestManualSubmissionValidation:
    """Test validation of manual submission data"""

    def test_manual_submission_amount_as_string(self, client):
        """Test that amount can be provided as string and is converted"""
        payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Store',
            'amount': '99.99',  # String
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-300',
            'comment': 'Amount test',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)

        assert response.status_code == 201
        history = get_submission_history()
        entry = next((e for e in history if e.get('po_number') == 'PO-2025-300'), None)
        assert entry['amount'] == 99.99

    def test_manual_submission_amount_as_float(self, client):
        """Test that amount can be provided as float"""
        payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Store',
            'amount': 45.50,  # Float
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-301',
            'comment': 'Float amount test',
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)

        assert response.status_code == 201
        history = get_submission_history()
        entry = next((e for e in history if e.get('po_number') == 'PO-2025-301'), None)
        assert entry['amount'] == 45.50

    def test_manual_submission_empty_comment_accepted(self, client):
        """Test that empty comment is accepted"""
        payload = {
            'student': 'Test Student A',
            'request_type': 'Reimbursement',
            'store_name': 'Store',
            'amount': '45.50',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'po_number': 'PO-2025-302',
            'comment': '',  # Empty comment
            'entry_date': '2025-11-15'
        }

        response = client.post('/api/manual-submission', json=payload)

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
