"""Pytest configuration and fixtures for ESA Helpers tests"""

import pytest
import json
import tempfile
from pathlib import Path
from app import create_app
from app.utils import delete_all_submissions


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True

    # Use temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        app.config['DATA_DIR'] = tmpdir
        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner"""
    return app.test_cli_runner()


@pytest.fixture(scope='session', autouse=True)
def cleanup_test_submissions():
    """Automatically clean up test submissions after all tests complete"""
    # This runs before any tests
    yield
    # This runs after all tests are complete
    print("\n\n🧹 Cleaning up test submissions (created_by='test')...")
    result = delete_all_submissions(created_by_filter='test')
    print(f"   {result['message']}\n")


@pytest.fixture
def sample_students():
    """Sample student data for testing"""
    return [
        {
            'id': 'student_b',
            'name': 'Student B',
            'folder': '/path/to/esa/student_b'
        },
        {
            'id': 'evie',
            'name': 'Student C',
            'folder': '/home/evie/esa'
        }
    ]


@pytest.fixture
def sample_vendors():
    """Sample vendor data for testing"""
    return [
        {
            'id': 'vendor1',
            'name': 'Math Tutor LLC',
            'type': 'Tutoring',
            'tax_rate': 0.05
        },
        {
            'id': 'vendor2',
            'name': 'Online Curriculum Inc',
            'type': 'Curriculum',
            'tax_rate': 0.0
        }
    ]


@pytest.fixture
def expense_categories():
    """Standard expense categories configuration"""
    return {
        'Computer Hardware & Technological Devices': {
            'required_fields': ['Receipt']
        },
        'Curriculum': {
            'required_fields': ['Receipt']
        },
        'Tutoring & Teaching Services - Accredited Facility/Business': {
            'required_fields': ['Receipt', 'Invoice']
        },
        'Tutoring & Teaching Services - Accredited Individual': {
            'required_fields': ['Receipt', 'Invoice', 'Attestation']
        },
        'Supplemental Materials (Curriculum Always Required)': {
            'required_fields': ['Curriculum', 'Receipt']
        }
    }


@pytest.fixture
def direct_pay_categories():
    """Direct Pay expense categories configuration"""
    return {
        'Computer Hardware & Technological Devices': {
            'required_fields': ['Invoice']
        },
        'Curriculum': {
            'required_fields': ['Invoice']
        },
        'Tutoring & Teaching Services - Accredited Facility/Business': {
            'required_fields': ['Invoice']
        },
        'Tutoring & Teaching Services - Accredited Individual': {
            'required_fields': ['Invoice']
        },
        'Supplemental Materials (Curriculum Always Required)': {
            'required_fields': ['Invoice', 'Curriculum']
        }
    }
