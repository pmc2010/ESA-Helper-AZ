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
