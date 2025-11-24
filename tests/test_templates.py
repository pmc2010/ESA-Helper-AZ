"""Tests for template CRUD operations"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestTemplateSaving:
    """Test template creation and saving"""

    def test_save_template_post_endpoint(self, client):
        """Test POST /api/templates endpoint saves template"""
        template_data = {
            'student_id': 'student_b',
            'name': 'Weekly Ice Skating',
            'vendor_id': 'vendor1',
            'request_type': 'Reimbursement',
            'amount': 50.00,
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'comment': 'Ice skating lesson',
            'files': {
                'Receipt': '/path/to/receipt',
                'Invoice': '/path/to/invoice',
                'Attestation': '/path/to/attestation'
            }
        }

        with patch('app.routes.save_student_template') as mock_save:
            mock_save.return_value = 'weekly_ice_skating_20250101120000'

            response = client.post('/api/templates',
                                  json=template_data,
                                  content_type='application/json')

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'template' in data
            assert data['template']['name'] == 'Weekly Ice Skating'

    def test_save_template_missing_required_fields(self, client):
        """Test POST /api/templates fails without required fields"""
        template_data = {
            'name': 'Weekly Ice Skating'
            # Missing student_id, vendor_id
        }

        response = client.post('/api/templates',
                              json=template_data,
                              content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_save_template_validates_vendor_id(self, client):
        """Test POST /api/templates requires vendor_id"""
        template_data = {
            'student_id': 'student_b',
            'name': 'Weekly Ice Skating'
            # Missing vendor_id
        }

        response = client.post('/api/templates',
                              json=template_data,
                              content_type='application/json')

        assert response.status_code == 400

    def test_save_template_with_direct_pay(self, client):
        """Test saving Direct Pay template"""
        template_data = {
            'student_id': 'student_b',
            'name': 'Direct Pay Tutoring',
            'vendor_id': 'vendor1',
            'request_type': 'Direct Pay',
            'amount': 75.00,
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'comment': 'Monthly tutoring',
            'files': {
                'Invoice': '/path/to/invoice'
            }
        }

        with patch('app.routes.save_student_template') as mock_save:
            mock_save.return_value = 'direct_pay_tutoring_20250101120000'

            response = client.post('/api/templates',
                                  json=template_data,
                                  content_type='application/json')

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['template']['request_type'] == 'Direct Pay'

    def test_save_template_with_file_paths(self, client):
        """Test template saves file paths correctly"""
        template_data = {
            'student_id': 'student_b',
            'name': 'Test Template',
            'vendor_id': 'vendor1',
            'files': {
                'Receipt': '/path/to/receipt/folder',
                'Invoice': '/path/to/invoice/file.pdf'
            }
        }

        with patch('app.routes.save_student_template') as mock_save:
            mock_save.return_value = 'test_template_20250101120000'

            response = client.post('/api/templates',
                                  json=template_data,
                                  content_type='application/json')

            assert response.status_code == 201
            # Verify save_student_template was called with correct data
            mock_save.assert_called_once()
            call_args = mock_save.call_args[0][0]
            assert call_args['files']['Receipt'] == '/path/to/receipt/folder'
            assert call_args['files']['Invoice'] == '/path/to/invoice/file.pdf'


class TestTemplateLoading:
    """Test template loading and retrieval"""

    def test_get_all_templates(self, client):
        """Test GET /api/templates returns all templates"""
        mock_templates = [
            {'id': 'template1', 'name': 'Template 1'},
            {'id': 'template2', 'name': 'Template 2'}
        ]

        with patch('app.routes.load_templates', return_value=mock_templates):
            response = client.get('/api/templates')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2

    def test_get_student_templates(self, client):
        """Test GET /api/templates/<student> returns student templates"""
        mock_student = {'id': 'student_b', 'name': 'Student B'}
        mock_templates = [
            {'id': 'template1', 'name': 'Template 1', 'student_id': 'student_b'}
        ]

        with patch('app.routes.load_student_profiles', return_value=[mock_student]), \
             patch('app.routes.load_student_templates', return_value=mock_templates):

            response = client.get('/api/templates/student_b')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 1

    def test_get_specific_template(self, client):
        """Test GET /api/template/<id> returns specific template"""
        mock_templates = [
            {'id': 'template1', 'name': 'My Template'}
        ]

        with patch('app.routes.load_templates', return_value=mock_templates):
            response = client.get('/api/template/template1')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['name'] == 'My Template'

    def test_get_template_not_found(self, client):
        """Test GET /api/template/<id> returns 404 for missing template"""
        with patch('app.routes.load_templates', return_value=[]):
            response = client.get('/api/template/nonexistent')

            assert response.status_code == 404


class TestTemplateDeletion:
    """Test template deletion"""

    def test_delete_template(self, client):
        """Test DELETE /api/templates/<student_id>/<template_id>"""
        with patch('app.routes.delete_student_template', return_value=True):
            response = client.delete('/api/templates/student_b/template1')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True

    def test_delete_template_not_found(self, client):
        """Test DELETE returns 404 if template not found"""
        with patch('app.routes.delete_student_template', return_value=False):
            response = client.delete('/api/templates/student_b/nonexistent')

            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data

    def test_delete_template_by_student_and_id(self, client):
        """Test DELETE correctly passes student_id and template_id"""
        with patch('app.routes.delete_student_template', return_value=True) as mock_delete:
            response = client.delete('/api/templates/student_b/my_template_12345')

            assert response.status_code == 200
            # Verify the function was called with correct arguments
            mock_delete.assert_called_once_with('student_b', 'my_template_12345')


class TestTemplateUtilityFunctions:
    """Test utility functions for templates"""

    def test_save_student_template_creates_new(self):
        """Test save_student_template creates new template"""
        from app.utils import save_student_template, load_student_templates

        template = {
            'id': 'test_template',
            'name': 'Test Template',
            'vendor_id': 'vendor1'
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = Path(tmpdir) / 'esa_templates'
            templates_dir.mkdir()

            with patch('app.utils.DATA_DIR', Path(tmpdir)):
                # Save template
                template_id = save_student_template(template, 'student_b')

                # Verify it was saved
                assert template_id == 'test_template'
                templates = load_student_templates('student_b')
                assert len(templates) == 1
                assert templates[0]['id'] == 'test_template'

    def test_save_student_template_updates_existing(self):
        """Test save_student_template updates existing template"""
        from app.utils import save_student_template, load_student_templates

        template1 = {
            'id': 'test_template',
            'name': 'Template 1',
            'vendor_id': 'vendor1'
        }

        template2 = {
            'id': 'test_template',
            'name': 'Template 1 Updated',
            'vendor_id': 'vendor2'
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = Path(tmpdir) / 'esa_templates'
            templates_dir.mkdir()

            with patch('app.utils.DATA_DIR', Path(tmpdir)):
                # Save first template
                save_student_template(template1, 'student_b')

                # Update template
                save_student_template(template2, 'student_b')

                # Verify only one template exists and it's updated
                templates = load_student_templates('student_b')
                assert len(templates) == 1
                assert templates[0]['vendor_id'] == 'vendor2'

    def test_delete_student_template(self):
        """Test delete_student_template removes template"""
        from app.utils import save_student_template, delete_student_template, load_student_templates

        template = {
            'id': 'test_template',
            'name': 'Test',
            'vendor_id': 'vendor1'
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = Path(tmpdir) / 'esa_templates'
            templates_dir.mkdir()

            with patch('app.utils.DATA_DIR', Path(tmpdir)):
                # Save template
                save_student_template(template, 'student_b')

                # Verify it exists
                templates = load_student_templates('student_b')
                assert len(templates) == 1

                # Delete it
                success = delete_student_template('student_b', 'test_template')
                assert success is True

                # Verify it's gone
                templates = load_student_templates('student_b')
                assert len(templates) == 0

    def test_delete_student_template_not_found(self):
        """Test delete_student_template returns False if not found"""
        from app.utils import delete_student_template

        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = Path(tmpdir) / 'esa_templates'
            templates_dir.mkdir()

            with patch('app.utils.DATA_DIR', Path(tmpdir)):
                # Try to delete non-existent template
                success = delete_student_template('student_b', 'nonexistent')
                assert success is False


class TestTemplateFileValidation:
    """Test template file path validation"""

    def test_template_saves_file_paths_as_required(self, client):
        """Test template saves with required file paths"""
        template_data = {
            'student_id': 'student_b',
            'name': 'Complete Template',
            'vendor_id': 'vendor1',
            'expense_category': 'Tutoring & Teaching Services - Accredited Individual',
            'files': {
                'Receipt': '/path/to/receipt',
                'Invoice': '/path/to/invoice',
                'Attestation': '/path/to/attestation'
            }
        }

        with patch('app.routes.save_student_template') as mock_save:
            mock_save.return_value = 'complete_template_20250101'

            response = client.post('/api/templates',
                                  json=template_data,
                                  content_type='application/json')

            assert response.status_code == 201
            call_args = mock_save.call_args[0][0]
            assert 'Receipt' in call_args['files']
            assert 'Invoice' in call_args['files']
            assert 'Attestation' in call_args['files']

    def test_template_saves_with_direct_pay_files(self, client):
        """Test Direct Pay template saves with Invoice and Curriculum"""
        template_data = {
            'student_id': 'taylor',
            'name': 'Direct Pay Supplemental',
            'vendor_id': 'vendor1',
            'request_type': 'Direct Pay',
            'expense_category': 'Supplemental Materials (Curriculum Always Required)',
            'files': {
                'Invoice': '/path/to/invoice',
                'Curriculum': '/path/to/curriculum'
            }
        }

        with patch('app.routes.save_student_template') as mock_save:
            mock_save.return_value = 'direct_pay_supplemental_20250101'

            response = client.post('/api/templates',
                                  json=template_data,
                                  content_type='application/json')

            assert response.status_code == 201
            call_args = mock_save.call_args[0][0]
            assert call_args['files']['Invoice'] == '/path/to/invoice'
            assert call_args['files']['Curriculum'] == '/path/to/curriculum'
            assert 'Receipt' not in call_args['files']


class TestTemplateIntegration:
    """Integration tests for template workflow"""

    def test_complete_template_workflow(self, client):
        """Test complete workflow: create, load, delete template"""
        # Create template
        template_data = {
            'student_id': 'student_b',
            'name': 'Weekly Lesson',
            'vendor_id': 'vendor1',
            'amount': 50.0,
            'expense_category': 'Curriculum',
            'files': {'Receipt': '/path/to/receipt'}
        }

        with patch('app.routes.save_student_template') as mock_save, \
             patch('app.routes.load_student_templates') as mock_load, \
             patch('app.routes.delete_student_template') as mock_delete:

            mock_save.return_value = 'weekly_lesson_20250101'
            mock_load.return_value = [template_data]
            mock_delete.return_value = True

            # Create
            response = client.post('/api/templates',
                                  json=template_data,
                                  content_type='application/json')
            assert response.status_code == 201

            # Load
            response = client.get('/api/templates/student_b')
            assert response.status_code == 200

            # Delete
            response = client.delete('/api/templates/student_b/weekly_lesson_20250101')
            assert response.status_code == 200
