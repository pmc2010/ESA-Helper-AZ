"""Pytest configuration and fixtures for ESA Helpers tests"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
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

        # Create students.json with test data
        data_dir = Path(tmpdir)
        students_file = data_dir / 'students.json'
        students_data = {
            'students': [
                {
                    'id': 'test_student_a',
                    'name': 'Test Student A',
                    'folder': str(data_dir / 'test_student_a'),
                    'allotment': 7500.00
                },
                {
                    'id': 'test_student_b',
                    'name': 'Test Student B',
                    'folder': str(data_dir / 'test_student_b'),
                    'allotment': 7500.00
                },
                {
                    'id': 'test_student_c',
                    'name': 'Test Student C',
                    'folder': str(data_dir / 'test_student_c'),
                    'allotment': 7500.00
                }
            ]
        }
        students_file.write_text(json.dumps(students_data, indent=2))

        # Create vendors.json with test data
        vendors_file = data_dir / 'vendors.json'
        vendors_data = {
            'vendors': [
                {
                    'id': 'test_vendor_1',
                    'name': 'Test Vendor LLC',
                    'classwallet_search_term': 'Test Vendor LLC',
                    'tax_rate': 0.0
                }
            ]
        }
        vendors_file.write_text(json.dumps(vendors_data, indent=2))

        yield app


@pytest.fixture
def client(app):
    """Create test client with mocked student/vendor loading"""
    # Mock the student loading in invoice_generator AND routes to return test data
    test_students = [
        {
            'id': 'test_student_a',
            'name': 'Test Student A',
            'folder': '/tmp/test_student_a',
            'allotment': 7500.00,
            'esa_allotments': []
        },
        {
            'id': 'test_student_b',
            'name': 'Test Student B',
            'folder': '/tmp/test_student_b',
            'allotment': 7500.00,
            'esa_allotments': []
        },
        {
            'id': 'test_student_c',
            'name': 'Test Student C',
            'folder': '/tmp/test_student_c',
            'allotment': 7500.00,
            'esa_allotments': []
        }
    ]

    # Patch both locations where load_student_profiles is imported
    with patch('app.invoice_generator.load_student_profiles', return_value=test_students), \
         patch('app.routes.load_student_profiles', return_value=test_students):
        yield app.test_client()


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
    import os
    from pathlib import Path

    print("\n\n🧹 Cleaning up test submissions...")

    # Delete test submission JSON files
    logs_dir = Path('logs')
    if logs_dir.exists():
        test_files_deleted = 0
        for f in logs_dir.glob('submission_*.json'):
            if f.name == 'submission_history.json':
                continue
            try:
                with open(f) as file:
                    content = file.read()
                    # Delete files containing test data or sample students
                    if ('"Test' in content or 'Test Category' in content or
                        'Student A' in content or 'Student B' in content or
                        'Student C' in content):
                        f.unlink()
                        test_files_deleted += 1
            except:
                pass

        if test_files_deleted > 0:
            print(f"   Deleted {test_files_deleted} test submission files")

    # Delete submissions marked with created_by='test' from history
    result = delete_all_submissions(created_by_filter='test')
    if 'Deleted 0' not in result['message']:
        print(f"   {result['message']}")

    # Also clean up history file from sample submissions
    try:
        history_file = logs_dir / 'submission_history.json'
        if history_file.exists():
            import json
            with open(history_file) as f:
                data = json.load(f)

            submissions = data.get('submissions', [])
            original_count = len(submissions)

            # Remove sample student submissions
            cleaned = [
                s for s in submissions
                if s.get('student', '') not in ['Student A', 'Student B', 'Student C']
            ]

            if len(cleaned) < original_count:
                data['submissions'] = cleaned
                with open(history_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"   Removed {original_count - len(cleaned)} sample submissions from history")
    except:
        pass

    # Clean up test data from students, vendors, and templates
    data_dir = Path('data')
    if data_dir.exists():
        import json

        # Clean students.json
        students_file = data_dir / 'students.json'
        if students_file.exists():
            try:
                with open(students_file) as f:
                    data = json.load(f)

                students = data.get('students', [])
                original_count = len(students)

                # Remove test students (new_student, Student A/B/C, etc.)
                cleaned = [
                    s for s in students
                    if s.get('id', '') not in ['new_student', 'student_a', 'student_b', 'student_c']
                    and s.get('name', '') not in ['Student A', 'Student B', 'Student C', 'New Student']
                ]

                if len(cleaned) < original_count:
                    data['students'] = cleaned
                    with open(students_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"   Removed {original_count - len(cleaned)} test students from data/students.json")
            except:
                pass

        # Clean templates for test students
        templates_dir = data_dir / 'esa_templates'
        if templates_dir.exists():
            for template_file in templates_dir.glob('*.json'):
                if template_file.name in ['student_a.json', 'student_b.json', 'student_c.json', 'new_student.json']:
                    try:
                        template_file.unlink()
                        print(f"   Deleted test template: {template_file.name}")
                    except:
                        pass

    print()


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
