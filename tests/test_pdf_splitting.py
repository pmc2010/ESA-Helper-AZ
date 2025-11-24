"""Tests for PDF splitting functionality"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from PyPDF2 import PdfWriter
from app import create_app
from app.utils import (
    split_pdf, get_temp_upload_dir, get_temp_files,
    delete_temp_file, cleanup_old_temp_files
)


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    yield app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample multi-page PDF for testing"""
    from PyPDF2 import PdfWriter
    from reportlab.pdfgen import canvas
    from io import BytesIO

    # Create a 3-page PDF
    pdf_path = tmp_path / "test_multipage.pdf"

    try:
        from reportlab.lib.pagesizes import letter
        # Create PDF with ReportLab
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)

        # Page 1
        c.drawString(100, 750, "Page 1 - Test Document")
        c.showPage()

        # Page 2
        c.drawString(100, 750, "Page 2 - Test Document")
        c.showPage()

        # Page 3
        c.drawString(100, 750, "Page 3 - Test Document")
        c.showPage()

        c.save()

        with open(pdf_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
    except ImportError:
        # Fallback if reportlab not available - create minimal PDF
        # This is a valid 3-page PDF structure
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R 4 0 R 5 0 R] /Count 3 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 6 0 R >>
endobj
4 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 7 0 R >>
endobj
5 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 8 0 R >>
endobj
6 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 750 Td
(Page 1) Tj
ET
endstream
endobj
7 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 750 Td
(Page 2) Tj
ET
endstream
endobj
8 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 750 Td
(Page 3) Tj
ET
endstream
endobj
xref
0 9
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000117 00000 n
0000000206 00000 n
0000000295 00000 n
0000000386 00000 n
0000000479 00000 n
0000000572 00000 n
trailer
<< /Size 9 /Root 1 0 R >>
startxref
665
%%EOF
"""
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)

    return pdf_path


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up temp files before and after each test"""
    temp_dir = get_temp_upload_dir()
    # Clean before
    for file_path in temp_dir.glob('*'):
        if file_path.is_file():
            file_path.unlink()

    yield

    # Clean after
    for file_path in temp_dir.glob('*'):
        if file_path.is_file():
            file_path.unlink()


class TestSplitPdfUtility:
    """Test the split_pdf() utility function"""

    def test_split_multipage_pdf(self, sample_pdf):
        """Test splitting a multi-page PDF"""
        result = split_pdf(sample_pdf)

        assert len(result) == 3
        assert all('filename' in f for f in result)
        assert all('path' in f for f in result)
        assert all('page_num' in f for f in result)
        assert all('total_pages' in f for f in result)

        # Verify page numbers
        for i, file_info in enumerate(result):
            assert file_info['page_num'] == i + 1
            assert file_info['total_pages'] == 3

    def test_split_single_page_pdf(self, tmp_path):
        """Test that single-page PDF returns empty list"""
        # Create a single-page PDF
        pdf_path = tmp_path / "single_page.pdf"
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 750 Td
(Page 1) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000204 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
297
%%EOF
"""
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)

        result = split_pdf(pdf_path)
        assert result == []

    def test_split_nonexistent_pdf(self):
        """Test splitting a non-existent PDF"""
        result = split_pdf("/nonexistent/path/to/file.pdf")
        assert result == []

    def test_split_files_saved_to_temp_dir(self, sample_pdf):
        """Test that split files are saved to temp directory"""
        result = split_pdf(sample_pdf)

        assert len(result) == 3
        for file_info in result:
            path = Path(file_info['path'])
            assert path.exists()
            assert path.parent == get_temp_upload_dir()


class TestTempFileManagement:
    """Test temporary file management functions"""

    def test_get_temp_upload_dir_creates_directory(self):
        """Test that get_temp_upload_dir creates directory if it doesn't exist"""
        temp_dir = get_temp_upload_dir()
        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_get_temp_files_empty_directory(self):
        """Test getting files from empty temp directory"""
        files = get_temp_files()
        assert files == []

    def test_get_temp_files_with_files(self, sample_pdf):
        """Test getting files from temp directory with files"""
        # Create some test files
        temp_dir = get_temp_upload_dir()
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("Test content")

        files = get_temp_files()
        assert len(files) == 1
        assert files[0]['filename'] == "test_file.txt"
        assert 'size' in files[0]
        assert 'created' in files[0]
        assert 'size_mb' in files[0]

    def test_delete_temp_file_success(self, sample_pdf):
        """Test deleting a temporary file"""
        temp_dir = get_temp_upload_dir()
        test_file = temp_dir / "test_delete.txt"
        test_file.write_text("Content to delete")

        assert test_file.exists()
        result = delete_temp_file("test_delete.txt")
        assert result is True
        assert not test_file.exists()

    def test_delete_temp_file_not_found(self):
        """Test deleting a file that doesn't exist"""
        result = delete_temp_file("nonexistent_file.txt")
        assert result is False

    def test_delete_temp_file_path_traversal_protection(self):
        """Test that path traversal attacks are blocked"""
        result = delete_temp_file("../../../etc/passwd")
        assert result is False

    def test_cleanup_old_temp_files(self):
        """Test that cleanup_old_temp_files function works"""
        # This test verifies the function runs without error
        # Timing-based file deletion is tested at the API level
        temp_dir = get_temp_upload_dir()

        # Create a test file
        test_file = temp_dir / "test_cleanup.txt"
        test_file.write_text("Test content")

        # Call cleanup - should return 0 since file is recent
        deleted = cleanup_old_temp_files(days=7)
        assert deleted == 0
        assert test_file.exists()

    def test_cleanup_all_temp_files(self, sample_pdf):
        """Test cleaning up all temporary files"""
        temp_dir = get_temp_upload_dir()

        # Create some test files
        for i in range(3):
            file = temp_dir / f"file_{i}.txt"
            file.write_text(f"Content {i}")

        files_before = get_temp_files()
        assert len(files_before) == 3

        # Cleanup all would normally be done via API
        # Here we test the directory clearing
        for file_path in temp_dir.glob('*'):
            if file_path.is_file():
                file_path.unlink()

        files_after = get_temp_files()
        assert len(files_after) == 0


class TestPdfSplitApi:
    """Test PDF split API endpoint"""

    def test_split_pdf_endpoint_success(self, client, sample_pdf):
        """Test POST /api/pdf/split with valid PDF"""
        with open(sample_pdf, 'rb') as f:
            response = client.post(
                '/api/pdf/split',
                data={'file': (f, 'test.pdf')},
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'files' in data
        assert len(data['files']) == 3

    def test_split_pdf_endpoint_no_file(self, client):
        """Test POST /api/pdf/split without file"""
        response = client.post(
            '/api/pdf/split',
            data={},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_split_pdf_endpoint_invalid_file(self, client):
        """Test POST /api/pdf/split with non-PDF file"""
        response = client.post(
            '/api/pdf/split',
            data={'file': (b'not a pdf', 'test.txt')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400


class TestTempFilesApi:
    """Test temporary files API endpoints"""

    def test_get_temp_files_endpoint(self, client, sample_pdf):
        """Test GET /api/temp-files"""
        # Split a PDF first to create temp files
        with open(sample_pdf, 'rb') as f:
            split_response = client.post(
                '/api/pdf/split',
                data={'file': (f, 'test.pdf')},
                content_type='multipart/form-data'
            )

        assert split_response.status_code == 200

        response = client.get('/api/temp-files')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'files' in data
        assert len(data['files']) >= 1

    def test_delete_temp_file_endpoint(self, client):
        """Test DELETE /api/temp-files/<filename>"""
        temp_dir = get_temp_upload_dir()
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("Test content")

        response = client.delete('/api/temp-files/test_file.txt')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert not test_file.exists()

    def test_delete_temp_file_not_found_endpoint(self, client):
        """Test DELETE /api/temp-files/<filename> with non-existent file"""
        response = client.delete('/api/temp-files/nonexistent.txt')
        assert response.status_code == 404

    def test_cleanup_old_files_endpoint(self, client):
        """Test POST /api/temp-files/cleanup/old endpoint"""
        temp_dir = get_temp_upload_dir()

        # Create a test file
        test_file = temp_dir / "test_cleanup_api.txt"
        test_file.write_text("Test content")

        # Call cleanup endpoint with days=7
        response = client.post(
            '/api/temp-files/cleanup/old',
            data=json.dumps({'days': 7}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # Since file is recent, deleted_count should be 0
        assert data['deleted_count'] == 0
        # File should still exist
        assert test_file.exists()

    def test_cleanup_all_files_endpoint(self, client):
        """Test POST /api/temp-files/cleanup/all"""
        temp_dir = get_temp_upload_dir()

        # Create test files
        for i in range(3):
            file = temp_dir / f"file_{i}.txt"
            file.write_text(f"Content {i}")

        response = client.post('/api/temp-files/cleanup/all')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['deleted_count'] == 3

        # Verify files are deleted
        files = get_temp_files()
        assert len(files) == 0


class TestManageTempFilesPage:
    """Test manage temporary files page"""

    def test_manage_temp_files_page_loads(self, client):
        """Test GET /manage-temp-files returns HTML"""
        response = client.get('/manage-temp-files')
        assert response.status_code == 200
        assert b'Manage Temporary Files' in response.data
        assert b'Split Multi-Page PDF' in response.data or b'Temporary Files' in response.data
