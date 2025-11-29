"""Tests for Flask routes and API endpoints"""

import pytest
import json
from unittest.mock import patch, MagicMock


class TestMainRoutes:
    """Test main page routes"""

    def test_index_redirects_without_config(self, client):
        """Test that index redirects to setup if no config"""
        with patch('app.routes.load_config', return_value=None):
            response = client.get('/')
            assert response.status_code == 302
            assert '/setup' in response.location

    def test_index_loads_with_config(self, client):
        """Test that index page loads with valid config"""
        mock_config = {'email': 'test@example.com'}
        with patch('app.routes.load_config', return_value=mock_config), \
             patch('app.routes.load_templates', return_value=[]), \
             patch('app.routes.load_vendors', return_value=[]), \
             patch('app.routes.load_student_profiles', return_value=[]):
            response = client.get('/')
            assert response.status_code == 200
            assert b'ESA Helper' in response.data

    def test_setup_page_loads(self, client):
        """Test setup page"""
        with patch('app.routes.load_config', return_value={}):
            response = client.get('/setup')
            assert response.status_code == 200

    def test_manage_students_page_loads(self, client):
        """Test manage students page"""
        with patch('app.routes.load_student_profiles', return_value=[]):
            response = client.get('/manage-students')
            assert response.status_code == 200

    def test_manage_vendors_page_loads(self, client):
        """Test manage vendors page"""
        with patch('app.routes.load_vendor_profiles', return_value=[]):
            response = client.get('/manage-vendors')
            assert response.status_code == 200

    def test_curriculum_generator_page_loads(self, client):
        """Test curriculum generator page"""
        with patch('app.routes.load_student_profiles', return_value=[]):
            response = client.get('/curriculum-generator')
            assert response.status_code == 200


class TestExpenseCategories:
    """Test expense category configuration"""

    def test_index_includes_reimbursement_categories(self, client):
        """Test that reimbursement categories are passed to template"""
        mock_config = {'email': 'test@example.com'}
        with patch('app.routes.load_config', return_value=mock_config), \
             patch('app.routes.load_templates', return_value=[]), \
             patch('app.routes.load_vendors', return_value=[]), \
             patch('app.routes.load_student_profiles', return_value=[]):
            response = client.get('/')
            assert response.status_code == 200
            # Check that categories are in the response
            assert b'Computer Hardware' in response.data

    def test_index_includes_direct_pay_categories(self, client):
        """Test that direct pay categories are passed to template"""
        mock_config = {'email': 'test@example.com'}
        with patch('app.routes.load_config', return_value=mock_config), \
             patch('app.routes.load_templates', return_value=[]), \
             patch('app.routes.load_vendors', return_value=[]), \
             patch('app.routes.load_student_profiles', return_value=[]):
            response = client.get('/')
            assert response.status_code == 200
            # Verify page loads successfully (categories are injected via JavaScript)
            assert b'Direct Pay' in response.data


class TestAPIEndpoints:
    """Test API endpoints"""

    def test_get_templates(self, client):
        """Test GET /api/templates endpoint"""
        mock_templates = [
            {'id': 'template1', 'name': 'Test Template'}
        ]
        with patch('app.routes.load_templates', return_value=mock_templates):
            response = client.get('/api/templates')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 1
            assert data[0]['id'] == 'template1'

    def test_get_student_templates(self, client):
        """Test GET /api/templates/<student> endpoint"""
        mock_student = {'id': 'student_b', 'name': 'Student B'}
        mock_templates = [
            {'id': 'template1', 'student_id': 'student_b'}
        ]
        with patch('app.routes.load_student_profiles', return_value=[mock_student]), \
             patch('app.routes.load_student_templates', return_value=mock_templates):
            response = client.get('/api/templates/student_b')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 1

    def test_get_template_not_found(self, client):
        """Test GET /api/template/<id> when template not found"""
        with patch('app.routes.load_templates', return_value=[]):
            response = client.get('/api/template/nonexistent')
            assert response.status_code == 404

    def test_get_vendors(self, client):
        """Test GET /api/vendors endpoint"""
        mock_vendors = [
            {'id': 'vendor1', 'name': 'Test Vendor'}
        ]
        with patch('app.routes.load_vendors', return_value=mock_vendors):
            response = client.get('/api/vendors')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 1

    def test_get_po_number(self, client):
        """Test GET /api/po-number endpoint"""
        with patch('app.routes.generate_po_number', return_value='PO-2024-001'):
            response = client.get('/api/po-number')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'po_number' in data or 'number' in data

    def test_get_credentials_status(self, client):
        """Test GET /api/config/credentials endpoint"""
        mock_config = {'email': 'test@example.com'}
        with patch('app.routes.load_config', return_value=mock_config):
            response = client.get('/api/config/credentials')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, dict)

    def test_get_auto_submit_setting(self, client):
        """Test GET /api/settings/auto-submit endpoint"""
        with patch('app.routes.load_config', return_value={'auto_submit': True}):
            response = client.get('/api/settings/auto-submit')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, dict)
