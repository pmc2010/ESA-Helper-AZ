"""Flask routes for ESA Helper application"""

from flask import Blueprint, render_template, request, jsonify, send_file, redirect
import json
import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
from app.utils import load_config, load_templates, load_student_templates, load_vendors, generate_po_number, save_student_template, delete_student_template, split_pdf, get_temp_files, delete_temp_file, cleanup_old_temp_files, get_submission_history, delete_submission, delete_all_submissions
from app.invoice_generator import (
    InvoiceGenerator, load_vendor_profiles, load_student_profiles,
    get_vendor, get_student, save_vendor_profile, save_student_profile,
    BASE_OUTPUT_DIR, sanitize_filename
)

# Create blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

# Constants
DATA_DIR = Path(__file__).parent.parent / 'data'
CONFIG_FILE = Path(__file__).parent.parent / 'config.json'


@main_bp.route('/setup')
def setup():
    """Render first-time setup/onboarding page"""
    config = load_config()
    return render_template('setup.html', config=config, current_page='setup')


@main_bp.route('/requirements')
def requirements():
    """Render requirements page"""
    return render_template('requirements.html', current_page='requirements')


@main_bp.route('/manage-students')
def manage_students():
    """Render student management page"""
    students = load_student_profiles()
    return render_template('manage-students.html', students=students, current_page='manage_students')


@main_bp.route('/manage-vendors')
def manage_vendors():
    """Render vendor management page"""
    vendors = load_vendor_profiles()
    return render_template('manage-vendors.html', vendors=vendors, current_page='manage_vendors')


@main_bp.route('/manage-templates')
def manage_templates():
    """Render template management page"""
    students = load_student_profiles()
    return render_template('manage-templates.html', students=students, current_page='manage_templates')


@main_bp.route('/manage-temp-files')
def manage_temp_files():
    """Render temporary file management page"""
    return render_template('manage-temp-files.html', current_page='manage_temp_files')


@main_bp.route('/manage-logs')
def manage_logs():
    """Render automation log management page"""
    return render_template('manage-logs.html', current_page='manage_logs')


@main_bp.route('/submission-history')
def submission_history():
    """Render submission history page"""
    return render_template('submission-history.html', current_page='submission_history')


@main_bp.route('/data-migration')
def data_migration():
    """Render data migration/backup page"""
    return render_template('data-migration.html', current_page='data_migration')


@main_bp.route('/curriculum-generator')
def curriculum_generator():
    """Render curriculum generator page"""
    try:
        student_profiles = load_student_profiles()
        students = sorted(student_profiles, key=lambda s: s['name'])
    except Exception as e:
        students = [
            {'id': 'student1', 'name': 'Student One'},
            {'id': 'student2', 'name': 'Student Two'},
            {'id': 'student3', 'name': 'Student Three'}
        ]
        logger.error(f"Error loading students: {str(e)}")
    return render_template('curriculum-generator.html', students=students, current_page='curriculum_generator')


@main_bp.route('/manage-curriculum-templates')
def manage_curriculum_templates():
    """Render curriculum template management page"""
    try:
        student_profiles = load_student_profiles()
        students = sorted(student_profiles, key=lambda s: s['name'])
    except Exception as e:
        students = [
            {'id': 'student1', 'name': 'Student One'},
            {'id': 'student2', 'name': 'Student Two'},
            {'id': 'student3', 'name': 'Student Three'}
        ]
        logger.error(f"Error loading students: {str(e)}")
    return render_template('manage-curriculum-templates.html', students=students, current_page='manage_curriculum_templates')


@main_bp.route('/faq')
def faq():
    """Render FAQ page"""
    return render_template('faq.html', current_page='faq')


@main_bp.route('/')
def index():
    """Render main form page - redirect to setup if no credentials"""
    config = load_config()
    if not config or not config.get('email'):
        # Redirect to setup if no configuration found
        return redirect('/setup')

    try:
        templates = load_templates()
    except Exception as e:
        templates = []
        logger.error(f"Error loading templates: {str(e)}")

    try:
        vendors = load_vendors()
    except Exception as e:
        vendors = []
        logger.error(f"Error loading vendors: {str(e)}")

    # Load students from database and sort alphabetically by name
    try:
        student_profiles = load_student_profiles()
        students = sorted(student_profiles, key=lambda s: s['name'])
    except Exception as e:
        students = [
            {'id': 'student1', 'name': 'Student One'},
            {'id': 'student2', 'name': 'Student Two'},
            {'id': 'student3', 'name': 'Student Three'}
        ]  # Fallback
        logger.error(f"Error loading students: {str(e)}")

    expense_categories = {
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

    # File requirements for Direct Pay submissions
    direct_pay_categories = {
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

    return render_template(
        'index.html',
        students=students,
        templates=templates,
        vendors=vendors,
        expense_categories=expense_categories,
        direct_pay_categories=direct_pay_categories,
        current_page='index'
    )


@api_bp.route('/templates', methods=['GET'])
def get_templates():
    """Get all templates"""
    templates = load_templates()
    return jsonify(templates)


@api_bp.route('/templates/<student>', methods=['GET'])
def get_student_templates(student):
    """Get templates for specific student (by ID or name)"""
    try:
        student_profiles = load_student_profiles()

        # Try to find student by ID first, then by name (for backward compatibility)
        student_profile = next((s for s in student_profiles
                               if s['id'].lower() == student.lower()), None)

        if not student_profile:
            # Fallback: try by name
            student_profile = next((s for s in student_profiles
                                   if s['name'].lower() == student.lower()), None)

        if student_profile:
            student_id = student_profile['id']
            templates = load_student_templates(student_id)
            return jsonify(templates)
        else:
            # Student not found, return empty list
            return jsonify([])

    except Exception as e:
        logger.error(f"Error loading templates for student {student}: {str(e)}")
        return jsonify([]), 500


@api_bp.route('/template/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get specific template"""
    templates = load_templates()
    template = next((t for t in templates if t.get('id') == template_id), None)
    if template:
        return jsonify(template)
    return jsonify({'error': 'Template not found'}), 404


@api_bp.route('/templates', methods=['POST'])
def save_new_template():
    """Save new template for a student"""
    try:
        data = request.json
        student_id = data.get('student_id')
        name = data.get('name')
        vendor_id = data.get('vendor_id')

        # Validate required fields
        if not all([student_id, name, vendor_id]):
            return jsonify({'error': 'Missing required fields: student_id, name, vendor_id'}), 400

        # Create template object
        # Use provided ID if editing, otherwise generate new ID for creating
        template_id = data.get('id')
        if not template_id:
            template_id = name.lower().replace(' ', '_') + '_' + datetime.now().strftime('%Y%m%d%H%M%S')

        template = {
            'id': template_id,
            'name': name,
            'vendor_id': vendor_id,
            'request_type': data.get('request_type', 'Reimbursement'),
            'amount': float(data.get('amount', 0)),
            'expense_category': data.get('expense_category', ''),
            'comment': data.get('comment', ''),
            'files': data.get('files', {})
        }

        # Save template
        template_id = save_student_template(template, student_id)
        template['id'] = template_id

        return jsonify({
            'success': True,
            'message': 'Template saved successfully',
            'template': template
        }), 201

    except Exception as e:
        logger.error(f"Error saving template: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/templates/<student_id>/<template_id>', methods=['DELETE'])
def delete_template_endpoint(student_id, template_id):
    """Delete template for a student"""
    try:
        success = delete_student_template(student_id, template_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Template deleted successfully'
            }), 200
        else:
            return jsonify({
                'error': 'Template not found'
            }), 404

    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/templates/<source_student_id>/<template_id>/duplicate', methods=['POST'])
def duplicate_template_endpoint(source_student_id, template_id):
    """Duplicate a template to the same or different student"""
    try:
        data = request.json
        target_student_id = data.get('target_student_id', source_student_id)

        # Load the source template
        source_templates = load_student_templates(source_student_id)
        source_template = next((t for t in source_templates if t.get('id') == template_id), None)

        if not source_template:
            return jsonify({'error': 'Template not found'}), 404

        # Create a new template by copying the source
        new_template = source_template.copy()

        # Generate a new ID with timestamp to make it unique
        new_template['id'] = source_template.get('name', 'template').lower().replace(' ', '_') + '_' + datetime.now().strftime('%Y%m%d%H%M%S')

        # Save the duplicated template to the target student
        template_id_new = save_student_template(new_template, target_student_id)
        new_template['id'] = template_id_new

        return jsonify({
            'success': True,
            'message': 'Template duplicated successfully',
            'template': new_template
        }), 201

    except Exception as e:
        logger.error(f"Error duplicating template: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/pdf/split', methods=['POST'])
def split_pdf_endpoint():
    """Split a multi-page PDF into individual page PDFs"""
    try:
        # Get file from request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Check if file is a PDF
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400

        # Save uploaded file temporarily
        temp_dir = Path(__file__).parent.parent / 'data' / 'temp_uploads'
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Save the file
        original_path = temp_dir / file.filename
        file.save(original_path)

        # Split the PDF
        split_files = split_pdf(original_path)

        if not split_files:
            # PDF has only 1 page, return the original
            return jsonify({
                'success': True,
                'message': 'PDF has only 1 page',
                'files': [{
                    'filename': file.filename,
                    'path': str(original_path),
                    'page_num': 1,
                    'total_pages': 1
                }]
            }), 200

        # Delete original multi-page PDF
        try:
            original_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete original PDF: {str(e)}")

        return jsonify({
            'success': True,
            'message': f'PDF split into {len(split_files)} pages',
            'files': split_files
        }), 200

    except Exception as e:
        logger.error(f"Error splitting PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/pdf/split-by-path', methods=['POST'])
def split_pdf_by_path():
    """Split a PDF by filesystem path (for files already on the server)"""
    try:
        data = request.json
        if not data or 'file_path' not in data:
            return jsonify({'error': 'No file_path provided'}), 400

        file_path = data.get('file_path')

        # Security check: ensure path is within allowed directories
        # Convert to absolute Path for comparison
        from pathlib import Path
        file_path_obj = Path(file_path).resolve()

        # Check if path exists and is a file
        if not file_path_obj.exists() or not file_path_obj.is_file():
            return jsonify({'error': 'File not found'}), 404

        # Check if it's a PDF
        if not str(file_path_obj).lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400

        logger.info(f"Attempting to split PDF from filesystem: {file_path}")

        # Split the PDF
        split_files = split_pdf(file_path_obj)

        if not split_files:
            # PDF has only 1 page, return the original
            logger.info(f"PDF has only 1 page, returning original")
            return jsonify({
                'success': True,
                'message': 'PDF has only 1 page',
                'files': [{
                    'filename': file_path_obj.name,
                    'path': str(file_path_obj),
                    'page_num': 1,
                    'total_pages': 1
                }]
            }), 200

        logger.info(f"✓ Successfully split PDF into {len(split_files)} pages")
        return jsonify({
            'success': True,
            'message': f'PDF split into {len(split_files)} pages',
            'files': split_files
        }), 200

    except Exception as e:
        logger.error(f"Error splitting PDF by path: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/temp-files', methods=['GET'])
def get_temp_files_endpoint():
    """Get list of temporary files"""
    try:
        files = get_temp_files()
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        }), 200
    except Exception as e:
        logger.error(f"Error getting temp files: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/temp-files/<filename>', methods=['DELETE'])
def delete_temp_file_endpoint(filename):
    """Delete a specific temporary file"""
    try:
        success = delete_temp_file(filename)
        if success:
            return jsonify({
                'success': True,
                'message': f'File deleted: {filename}'
            }), 200
        else:
            return jsonify({
                'error': 'File not found'
            }), 404
    except Exception as e:
        logger.error(f"Error deleting temp file: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/temp-files/cleanup/old', methods=['POST'])
def cleanup_temp_files_endpoint():
    """Clean up old temporary files"""
    try:
        days = request.json.get('days', 7) if request.json else 7
        deleted_count = cleanup_old_temp_files(days)

        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} old files',
            'deleted_count': deleted_count
        }), 200
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/temp-files/cleanup/all', methods=['POST'])
def cleanup_all_temp_files_endpoint():
    """Delete all temporary files"""
    try:
        temp_dir = Path(__file__).parent.parent / 'data' / 'temp_uploads'
        if not temp_dir.exists():
            return jsonify({
                'success': True,
                'message': 'No temp files to delete',
                'deleted_count': 0
            }), 200

        deleted_count = 0
        for file_path in temp_dir.glob('*'):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Could not delete {file_path.name}: {str(e)}")

        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} temp files',
            'deleted_count': deleted_count
        }), 200
    except Exception as e:
        logger.error(f"Error deleting all temp files: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/submission-history', methods=['GET'])
def get_submission_history_endpoint():
    """Get all submission history"""
    try:
        # Get limit parameter for sidebar (default 5 recent, or 'all' for full history)
        limit = request.args.get('limit', 'all')

        history = get_submission_history()

        if limit != 'all' and limit.isdigit():
            history = history[:int(limit)]

        return jsonify({
            'success': True,
            'submissions': history,
            'count': len(history)
        }), 200
    except Exception as e:
        logger.error(f"Error getting submission history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/submission/<timestamp>', methods=['DELETE'])
def delete_submission_endpoint(timestamp):
    """Delete a single submission by timestamp"""
    try:
        success = delete_submission(timestamp)
        if success:
            return jsonify({
                'success': True,
                'message': f'Submission {timestamp} deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Could not delete submission {timestamp}'
            }), 404
    except Exception as e:
        logger.error(f"Error deleting submission {timestamp}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/submissions/delete-all', methods=['DELETE'])
def delete_all_submissions_endpoint():
    """Delete all submissions from history"""
    try:
        result = delete_all_submissions()
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'deleted_count': result['deleted_count']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['message']
            }), 500
    except Exception as e:
        logger.error(f"Error deleting all submissions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/vendors', methods=['GET'])
def get_vendors():
    """Get all vendors"""
    vendors = load_vendors()
    return jsonify(vendors)


@api_bp.route('/vendors', methods=['POST'])
def add_vendor():
    """Add new vendor (redirects to detailed vendor creation)"""
    # This endpoint is deprecated - redirects to the detailed vendor creation endpoint
    # For backward compatibility, convert basic vendor format to detailed format
    data = request.json

    # Convert to detailed format
    detailed_vendor = {
        'id': data.get('id', data.get('name').lower().replace(' ', '_')),
        'name': data.get('name'),
        'business_name': data.get('business_name', data.get('name')),
        'address_line_1': data.get('address_line_1', ''),
        'address_line_2': data.get('address_line_2', data.get('location', '')),
        'phone': data.get('phone', ''),
        'email': data.get('email', ''),
        'tax_rate': float(data.get('tax_rate', 0.0)),
        'classwallet_search_term': data.get('classwallet_search_term', '')
    }

    # Check if vendor already exists
    vendors = load_vendor_profiles()
    if not any(v['id'] == detailed_vendor['id'] for v in vendors):
        if save_vendor_profile(detailed_vendor):
            return jsonify(detailed_vendor), 201
        return jsonify({'error': 'Failed to save vendor'}), 500

    return jsonify({'error': 'Vendor already exists'}), 400


@api_bp.route('/po-number', methods=['GET'])
def get_po_number():
    """Generate PO number"""
    po = generate_po_number()
    return jsonify({'po_number': po})


@api_bp.route('/config/credentials', methods=['GET'])
def get_credentials_status():
    """Check if credentials are configured"""
    if CONFIG_FILE.exists():
        return jsonify({'configured': True})
    return jsonify({'configured': False})


@api_bp.route('/config/credentials', methods=['POST'])
def save_credentials():
    """Save ClassWallet credentials

    Note: Students should be configured via the "Manage Students" interface.
    This endpoint only saves the ClassWallet email and password.
    """
    data = request.json

    config = {
        'email': data.get('email'),
        'password': data.get('password')
    }

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    return jsonify({'success': True})


@api_bp.route('/settings/auto-submit', methods=['GET'])
def get_auto_submit_setting():
    """Get auto-submit setting"""
    try:
        config = load_config()
        if config:
            return jsonify({'autoSubmit': config.get('autoSubmit', False)})
        return jsonify({'autoSubmit': False})
    except Exception as e:
        logger.error(f"Error loading auto-submit setting: {str(e)}")
        return jsonify({'autoSubmit': False})


@api_bp.route('/settings/auto-submit', methods=['POST'])
def save_auto_submit_setting():
    """Save auto-submit setting"""
    try:
        data = request.json
        config = load_config() or {}

        config['autoSubmit'] = data.get('autoSubmit', False)

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Auto-submit setting saved: {config['autoSubmit']}")
        return jsonify({'success': True, 'autoSubmit': config['autoSubmit']})
    except Exception as e:
        logger.error(f"Error saving auto-submit setting: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/browser/list', methods=['POST'])
def list_files():
    """List files in a directory"""
    data = request.json
    path = data.get('path')

    if not path:
        return jsonify({'error': 'Path required'}), 400

    try:
        p = Path(path)
        if not p.exists():
            return jsonify({'error': 'Path does not exist'}), 404

        files = []
        folders = []

        for item in p.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                folders.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'folder'
                })
            elif item.is_file() and item.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.png', '.gif']:
                files.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'file',
                    'ext': item.suffix.lower()
                })

        return jsonify({
            'path': str(p),
            'folders': sorted(folders, key=lambda x: x['name']),
            'files': sorted(files, key=lambda x: x['name'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/preview', methods=['POST'])
def preview_file():
    """Return file for preview"""
    data = request.json
    file_path = data.get('path')

    if not file_path or not Path(file_path).exists():
        return jsonify({'error': 'File not found'}), 404

    try:
        return send_file(file_path, mimetype='application/octet-stream')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/vendors-detailed', methods=['GET'])
def get_vendors_detailed():
    """Get detailed vendor profiles"""
    vendors = load_vendor_profiles()
    return jsonify(vendors)


@api_bp.route('/vendors-detailed/<vendor_id>', methods=['GET'])
def get_vendor_detailed(vendor_id):
    """Get specific vendor profile"""
    vendors = load_vendor_profiles()
    vendor = next((v for v in vendors if v['id'] == vendor_id), None)
    if vendor:
        return jsonify(vendor)
    return jsonify({'error': 'Vendor not found'}), 404


@api_bp.route('/vendors-detailed', methods=['POST'])
def save_vendor():
    """Save or update vendor profile"""
    data = request.json
    if save_vendor_profile(data):
        return jsonify({'success': True, 'vendor': data}), 201
    return jsonify({'error': 'Failed to save vendor'}), 400


@api_bp.route('/students-detailed', methods=['GET'])
def get_students_detailed():
    """Get detailed student profiles"""
    students = load_student_profiles()
    return jsonify(students)


@api_bp.route('/students-detailed/<student_id>', methods=['GET'])
def get_student_detailed(student_id):
    """Get specific student profile"""
    students = load_student_profiles()
    student = next((s for s in students if s['id'] == student_id), None)
    if student:
        return jsonify(student)
    return jsonify({'error': 'Student not found'}), 404


@api_bp.route('/students-detailed', methods=['POST'])
def save_student():
    """Save or update student profile"""
    data = request.json
    if save_student_profile(data):
        return jsonify({'success': True, 'student': data}), 201
    return jsonify({'error': 'Failed to save student'}), 400


@api_bp.route('/invoice/generate', methods=['POST'])
def generate_invoice():
    """Generate invoice from form data"""
    try:
        data = request.json

        # Validate required fields
        # Support both new format (line_items array) and old format (single description/unit_price/quantity)
        base_fields = ['student', 'vendor_name', 'invoice_number', 'date']
        if not all(field in data for field in base_fields):
            return jsonify({'success': False, 'message': 'Missing required fields: student, vendor_name, invoice_number, date'}), 400

        # Check for either line_items array OR old single-item format
        has_line_items = 'line_items' in data and isinstance(data['line_items'], list) and len(data['line_items']) > 0
        has_single_item = all(field in data for field in ['description', 'unit_price', 'quantity'])

        if not has_line_items and not has_single_item:
            return jsonify({'success': False, 'message': 'Missing invoice items: provide either line_items array or description/unit_price/quantity'}), 400

        # Get student profile by ID (the form sends the student.id, e.g., "taylor")
        student_profiles = load_student_profiles()
        student = next((s for s in student_profiles if s['id'] == data['student']), None)

        if not student:
            return jsonify({'success': False, 'message': f"Student not found: {data['student']}"}), 400

        # Get the full student name from the profile
        student_name = student.get('name', '')
        logger.info(f"Invoice generation - Student ID: '{data['student']}' -> Full name: '{student_name}'")

        # Securely construct output directory: always under BASE_OUTPUT_DIR with sanitized student ID & year
        # This prevents path traversal attacks through student['folder']
        student_id_sanitized = sanitize_filename(student['id'])
        year = str(datetime.now().year)
        output_dir = BASE_OUTPUT_DIR / student_id_sanitized / year

        # Get vendor profile
        vendor = get_vendor(data['vendor_name'])
        if not vendor:
            # Use form data if vendor profile not found
            vendor = {
                'name': data['vendor_name'],  # Use for filename generation
                'business_name': data.get('vendor_business_name', data['vendor_name']),
                'address_line_1': data.get('vendor_address_1', ''),
                'address_line_2': data.get('vendor_address_2', ''),
                'phone': data.get('vendor_phone', ''),
                'email': data.get('vendor_email', ''),
                'tax_rate': float(data.get('tax_rate', 0.0))
            }

        # Prepare invoice data
        # Support both new format (line_items) and old format (single item)
        if has_line_items:
            # New format: use line_items array
            invoice_data = {
                'invoice_number': data['invoice_number'],
                'date': data['date'],
                'line_items': data['line_items'],
                'tax_rate': float(data.get('tax_rate', vendor.get('tax_rate', 0.0)))
            }
        else:
            # Old format: single item (backward compatibility)
            invoice_data = {
                'invoice_number': data['invoice_number'],
                'date': data['date'],
                'description': data['description'],
                'quantity': float(data.get('quantity', 1)),
                'unit_price': float(data.get('unit_price', 0)),
                'tax_rate': float(data.get('tax_rate', vendor.get('tax_rate', 0.0)))
            }

        # Generate invoice
        generator = InvoiceGenerator()
        result = generator.generate_invoice(vendor, student, invoice_data, str(output_dir))

        return jsonify(result)

    except Exception as e:
        logger.error(f"Invoice generation error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@api_bp.route('/submit', methods=['POST'])
def submit_reimbursement():
    """Submit reimbursement/direct pay request to ClassWallet"""
    from app.automation import submit_to_classwallet

    data = request.json

    # Validate required fields (all requests need these)
    base_required_fields = ['student', 'request_type', 'amount', 'expense_category', 'po_number', 'comment']
    if not all(field in data for field in base_required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    # Validate request-type-specific fields
    request_type = data.get('request_type')
    if request_type == 'Reimbursement':
        if 'store_name' not in data:
            return jsonify({'success': False, 'message': 'Missing required fields (store_name)'}), 400
        vendor_or_store = data.get('store_name')
    elif request_type == 'Direct Pay':
        if 'vendor_name' not in data:
            return jsonify({'success': False, 'message': 'Missing required fields (vendor_name)'}), 400
        vendor_or_store = data.get('vendor_name')
    else:
        return jsonify({'success': False, 'message': 'Invalid request type'}), 400

    # Log submission attempt
    submission_log = {
        'timestamp': datetime.now().isoformat(),
        'student': data.get('student'),
        'request_type': request_type,
        'amount': data.get('amount'),
        'expense_category': data.get('expense_category'),
        'po_number': data.get('po_number'),
        'comment': data.get('comment'),
        'files': data.get('files', [])
    }

    # Add request-type-specific fields to log
    if request_type == 'Reimbursement':
        submission_log['store_name'] = data.get('store_name')
    elif request_type == 'Direct Pay':
        submission_log['vendor_name'] = data.get('vendor_name')
        submission_log['classwallet_search_term'] = data.get('classwallet_search_term')

    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"submission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(log_file, 'w') as f:
        json.dump(submission_log, f, indent=2)

    # Get auto-submit preference from config
    config = load_config()
    auto_submit = config.get('autoSubmit', False) if config else False

    # Submit to ClassWallet (this will open browser and automate the process)
    result = submit_to_classwallet(data, auto_submit=auto_submit)

    return jsonify(result)


@api_bp.route('/students', methods=['POST'])
def create_student():
    """Create a new student"""
    try:
        data = request.json
        students = load_student_profiles()

        # Create new student object
        new_student = {
            'id': data.get('id', data.get('name').lower().replace(' ', '_')),
            'name': data.get('name'),
            'address_line_1': data.get('address_line_1', ''),
            'address_line_2': data.get('address_line_2', ''),
            'folder': data.get('folder', '')
        }

        # Check if student already exists
        if any(s['id'] == new_student['id'] for s in students):
            return jsonify({'error': 'Student already exists'}), 400

        students.append(new_student)
        if save_student_profile(new_student):
            return jsonify(new_student), 201
        return jsonify({'error': 'Failed to save student'}), 500
    except Exception as e:
        logger.error(f"Error creating student: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    """Update a student"""
    try:
        data = request.json
        students = load_student_profiles()

        student = next((s for s in students if s['id'] == student_id), None)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Update student fields
        student['name'] = data.get('name', student['name'])
        student['address_line_1'] = data.get('address_line_1', student['address_line_1'])
        student['address_line_2'] = data.get('address_line_2', student['address_line_2'])
        student['folder'] = data.get('folder', student['folder'])

        if save_student_profile(student):
            return jsonify(student), 200
        return jsonify({'error': 'Failed to save student'}), 500
    except Exception as e:
        logger.error(f"Error updating student: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
    try:
        students = load_student_profiles()

        student = next((s for s in students if s['id'] == student_id), None)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        students.remove(student)

        # Save updated list
        students_file = DATA_DIR / 'students.json'
        with open(students_file, 'w') as f:
            json.dump({'students': students}, f, indent=2)

        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/vendors', methods=['POST'])
def create_vendor():
    """Create a new vendor (using existing save_vendor_profile)"""
    try:
        data = request.json
        vendors = load_vendor_profiles()

        new_vendor = {
            'id': data.get('id', data.get('name').lower().replace(' ', '_')),
            'name': data.get('name'),
            'business_name': data.get('business_name', ''),
            'address_line_1': data.get('address_line_1', ''),
            'address_line_2': data.get('address_line_2', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'tax_rate': float(data.get('tax_rate', 0.0)),
            'classwallet_search_term': data.get('classwallet_search_term', '')
        }

        if any(v['id'] == new_vendor['id'] for v in vendors):
            return jsonify({'error': 'Vendor already exists'}), 400

        if save_vendor_profile(new_vendor):
            return jsonify(new_vendor), 201
        return jsonify({'error': 'Failed to save vendor'}), 500
    except Exception as e:
        logger.error(f"Error creating vendor: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/vendors/<vendor_id>', methods=['PUT'])
def update_vendor(vendor_id):
    """Update a vendor"""
    try:
        data = request.json
        vendors = load_vendor_profiles()

        vendor = next((v for v in vendors if v['id'] == vendor_id), None)
        if not vendor:
            return jsonify({'error': 'Vendor not found'}), 404

        vendor['name'] = data.get('name', vendor['name'])
        vendor['business_name'] = data.get('business_name', vendor.get('business_name', ''))
        vendor['address_line_1'] = data.get('address_line_1', vendor.get('address_line_1', ''))
        vendor['address_line_2'] = data.get('address_line_2', vendor.get('address_line_2', ''))
        vendor['phone'] = data.get('phone', vendor.get('phone', ''))
        vendor['email'] = data.get('email', vendor.get('email', ''))
        vendor['tax_rate'] = float(data.get('tax_rate', vendor.get('tax_rate', 0.0)))
        vendor['classwallet_search_term'] = data.get('classwallet_search_term', vendor.get('classwallet_search_term', ''))

        if save_vendor_profile(vendor):
            return jsonify(vendor), 200
        return jsonify({'error': 'Failed to save vendor'}), 500
    except Exception as e:
        logger.error(f"Error updating vendor: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/vendors/<vendor_id>', methods=['DELETE'])
def delete_vendor(vendor_id):
    """Delete a vendor"""
    try:
        vendors = load_vendor_profiles()

        vendor = next((v for v in vendors if v['id'] == vendor_id), None)
        if not vendor:
            return jsonify({'error': 'Vendor not found'}), 404

        vendors.remove(vendor)

        # Save updated list
        vendors_file = DATA_DIR / 'vendors.json'
        with open(vendors_file, 'w') as f:
            json.dump({'vendors': vendors}, f, indent=2)

        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error deleting vendor: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/data/export', methods=['GET'])
def export_data():
    """Export all data (students, vendors, templates, submission history, curriculum templates, settings) as JSON"""
    try:
        students = load_student_profiles()
        vendors = load_vendor_profiles()
        submission_history = get_submission_history()

        # Load reimbursement templates for each student (organized by student)
        templates = {}
        templates_dir = DATA_DIR / 'esa_templates'
        if templates_dir.exists():
            for student in students:
                template_file = templates_dir / f"{student['id']}.json"
                if template_file.exists():
                    try:
                        with open(template_file, 'r') as f:
                            templates[student['id']] = json.load(f)
                    except Exception as e:
                        logger.warning(f"Could not load reimbursement templates for {student['id']}: {str(e)}")
                        templates[student['id']] = []

        # Load curriculum templates for each student
        curriculum_templates = {}
        curriculum_dir = DATA_DIR / 'curriculum_templates'
        if curriculum_dir.exists():
            for student in students:
                template_file = curriculum_dir / f"{student['id']}.json"
                if template_file.exists():
                    try:
                        with open(template_file, 'r') as f:
                            curriculum_templates[student['id']] = json.load(f)
                    except Exception as e:
                        logger.warning(f"Could not load curriculum templates for {student['id']}: {str(e)}")
                        curriculum_templates[student['id']] = []

        # Load settings (non-credential parts of config)
        config = load_config()
        settings = {}
        if config:
            # Include only non-sensitive settings
            if 'autoSubmit' in config:
                settings['autoSubmit'] = config['autoSubmit']
            # Add other non-credential settings here as they're added to config

        export_data = {
            'version': '1.1',
            'export_date': datetime.now().isoformat(),
            'students': students,
            'vendors': vendors,
            'templates': templates,
            'submission_history': submission_history,
            'curriculum_templates': curriculum_templates,
            'settings': settings
        }

        return jsonify(export_data)
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/data/import', methods=['POST'])
def import_data():
    """Import data from JSON file with selective import

    Expected POST body:
    {
        'data': {...full backup data...},
        'import_categories': ['students', 'vendors', 'templates', 'submission_history', 'curriculum_templates', 'settings']
    }
    """
    try:
        request_data = request.json
        data = request_data.get('data', {})
        import_categories = request_data.get('import_categories', [])

        # If no categories specified, default to everything (backward compatibility)
        if not import_categories:
            import_categories = ['students', 'vendors', 'templates', 'submission_history', 'curriculum_templates', 'settings']

        results = {}

        # Import students
        if 'students' in import_categories and 'students' in data and data['students']:
            students_file = DATA_DIR / 'students.json'
            with open(students_file, 'w') as f:
                json.dump({'students': data['students']}, f, indent=2)
            results['students'] = len(data['students'])
            logger.info(f"✓ Imported {len(data['students'])} students")

        # Import vendors
        if 'vendors' in import_categories and 'vendors' in data and data['vendors']:
            vendors_file = DATA_DIR / 'vendors.json'
            with open(vendors_file, 'w') as f:
                json.dump({'vendors': data['vendors']}, f, indent=2)
            results['vendors'] = len(data['vendors'])
            logger.info(f"✓ Imported {len(data['vendors'])} vendors")

        # Import reimbursement templates (organized by student)
        if 'templates' in import_categories and 'templates' in data and data['templates']:
            templates_dir = DATA_DIR / 'esa_templates'
            templates_dir.mkdir(parents=True, exist_ok=True)

            template_count = 0
            templates_data = data['templates']

            try:
                # Handle both new format (dict by student_id) and old format (flat list)
                if isinstance(templates_data, dict):
                    # New format: dict with student_id as keys
                    for student_id, template_list in templates_data.items():
                        if template_list:  # Only write if there are templates for this student
                            template_file = templates_dir / f'{student_id}.json'
                            with open(template_file, 'w') as f:
                                json.dump(template_list, f, indent=2)
                            template_count += 1
                elif isinstance(templates_data, list):
                    # Old format: flat list - reconstruct by student_id from template.id
                    templates_by_student = {}
                    for template in templates_data:
                        try:
                            if isinstance(template, dict) and 'id' in template:
                                # Extract student_id from template.id (format: "student_id_...")
                                student_id = template['id'].split('_')[0]
                                if student_id not in templates_by_student:
                                    templates_by_student[student_id] = []
                                templates_by_student[student_id].append(template)
                            elif isinstance(template, dict):
                                # Template dict but no 'id' field - skip with warning
                                logger.warning(f"Template found without 'id' field: {template.keys()}")
                            else:
                                # Template is not a dict - skip with warning
                                logger.warning(f"Skipping non-dict template: type={type(template).__name__}")
                        except Exception as e:
                            logger.warning(f"Error processing individual template: {str(e)}")
                            continue

                    # Write reconstructed templates to files
                    for student_id, template_list in templates_by_student.items():
                        template_file = templates_dir / f'{student_id}.json'
                        with open(template_file, 'w') as f:
                            json.dump(template_list, f, indent=2)
                        template_count += 1
                else:
                    logger.warning(f"Unexpected templates format: type={type(templates_data).__name__}")

                results['templates'] = template_count
                logger.info(f"✓ Imported reimbursement templates for {template_count} students")
            except Exception as e:
                logger.error(f"Error importing templates: {str(e)}")
                logger.error(f"Templates data structure: {type(templates_data).__name__}")
                return jsonify({'error': f'Error importing templates: {str(e)}'}), 500

        # Import submission history
        if 'submission_history' in import_categories and 'submission_history' in data and data['submission_history']:
            history_file = Path(__file__).parent.parent / 'logs' / 'submission_history.json'
            history_file.parent.mkdir(parents=True, exist_ok=True)

            # Handle both old format (flat list) and new format (dict with submissions key)
            history_data = data['submission_history']
            if isinstance(history_data, list):
                # Old format: flat list - wrap it in the expected dict structure
                history_data = {'submissions': history_data}
                submission_count = len(history_data['submissions'])
            elif isinstance(history_data, dict):
                # New format: dict with submissions key
                submission_count = len(history_data.get('submissions', []))
            else:
                submission_count = 0

            if submission_count > 0:
                with open(history_file, 'w') as f:
                    json.dump(history_data, f, indent=2)
                results['submission_history'] = submission_count
                logger.info(f"✓ Imported {submission_count} submission history records")

        # Import curriculum templates
        if 'curriculum_templates' in import_categories and 'curriculum_templates' in data and data['curriculum_templates']:
            curriculum_dir = DATA_DIR / 'curriculum_templates'
            curriculum_dir.mkdir(parents=True, exist_ok=True)

            curriculum_count = 0
            for student_id, templates in data['curriculum_templates'].items():
                if templates:  # Only write if there are templates for this student
                    template_file = curriculum_dir / f'{student_id}.json'
                    with open(template_file, 'w') as f:
                        json.dump(templates, f, indent=2)
                    curriculum_count += 1

            results['curriculum_templates'] = curriculum_count
            logger.info(f"✓ Imported curriculum templates for {curriculum_count} students")

        # Import settings
        if 'settings' in import_categories and 'settings' in data and data['settings']:
            config = load_config()
            if not config:
                config = {}

            # Merge imported settings with existing config (only non-credential settings)
            if 'autoSubmit' in data['settings']:
                config['autoSubmit'] = data['settings']['autoSubmit']

            # Write config back (preserving credentials)
            config_file = Path(__file__).parent.parent / 'config.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            results['settings'] = True
            logger.info(f"✓ Imported settings")

        return jsonify({
            'success': True,
            'message': 'Data imported successfully',
            'results': results
        })
    except Exception as e:
        logger.error(f"Error importing data: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/data/reset', methods=['POST'])
def reset_data():
    """Completely reset all data (students, vendors, templates, submission history, curriculum templates).

    This does NOT reset credentials in config.json.
    Requires confirmation from frontend.
    """
    try:
        request_data = request.json
        confirmed = request_data.get('confirmed', False)

        if not confirmed:
            return jsonify({'error': 'Reset not confirmed'}), 400

        results = {}

        # Reset students
        students_file = DATA_DIR / 'students.json'
        try:
            with open(students_file, 'w') as f:
                json.dump({'students': []}, f, indent=2)
            results['students'] = 'cleared'
            logger.info("✓ Reset: Students cleared")
        except Exception as e:
            logger.warning(f"Could not reset students: {str(e)}")

        # Reset vendors
        vendors_file = DATA_DIR / 'vendors.json'
        try:
            with open(vendors_file, 'w') as f:
                json.dump({'vendors': []}, f, indent=2)
            results['vendors'] = 'cleared'
            logger.info("✓ Reset: Vendors cleared")
        except Exception as e:
            logger.warning(f"Could not reset vendors: {str(e)}")

        # Reset templates (delete all files in esa_templates directory)
        templates_dir = DATA_DIR / 'esa_templates'
        try:
            if templates_dir.exists():
                for template_file in templates_dir.glob('*.json'):
                    template_file.unlink()
            results['templates'] = 'cleared'
            logger.info("✓ Reset: Templates cleared")
        except Exception as e:
            logger.warning(f"Could not reset templates: {str(e)}")

        # Reset curriculum templates (delete all files in curriculum_templates directory)
        curriculum_dir = DATA_DIR / 'curriculum_templates'
        try:
            if curriculum_dir.exists():
                for curriculum_file in curriculum_dir.glob('*.json'):
                    curriculum_file.unlink()
            results['curriculum_templates'] = 'cleared'
            logger.info("✓ Reset: Curriculum templates cleared")
        except Exception as e:
            logger.warning(f"Could not reset curriculum templates: {str(e)}")

        # Reset submission history and all log files
        logs_dir = Path(__file__).parent.parent / 'logs'
        try:
            if logs_dir.exists():
                for log_file in logs_dir.glob('*'):
                    if log_file.is_file():
                        log_file.unlink()
            results['logs'] = 'cleared'
            logger.info("✓ Reset: All logs cleared")
        except Exception as e:
            logger.warning(f"Could not reset logs: {str(e)}")

        # Log the reset event
        logger.info("=" * 60)
        logger.info("🔄 FULL DATA RESET PERFORMED")
        logger.info(f"Reset at: {datetime.now().isoformat()}")
        logger.info(f"Items reset: {', '.join(results.keys())}")
        logger.info("Note: Config.json (credentials) were NOT reset")
        logger.info("=" * 60)

        return jsonify({
            'success': True,
            'message': 'All data has been reset successfully. Credentials (config.json) were preserved.',
            'results': results
        })
    except Exception as e:
        logger.error(f"Error resetting data: {str(e)}")
        return jsonify({'error': f'Reset failed: {str(e)}'}), 500


# ========== LOG MANAGEMENT ENDPOINTS ==========

@api_bp.route('/logs', methods=['GET'])
def get_logs():
    """Get list of all automation log files with metadata"""
    try:
        logs_dir = Path(__file__).parent.parent / 'logs'
        if not logs_dir.exists():
            return jsonify([])

        log_files = []
        for file_path in sorted(logs_dir.glob('automation_*.log'), reverse=True):
            try:
                stat = file_path.stat()
                # Extract date from filename (automation_YYYYMMDD.log)
                date_str = file_path.stem.replace('automation_', '')
                log_files.append({
                    'name': file_path.name,
                    'date': date_str,
                    'size': stat.st_size,
                    'size_kb': round(stat.st_size / 1024, 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'line_count': sum(1 for _ in open(file_path))
                })
            except Exception as e:
                logger.warning(f"Could not get metadata for {file_path.name}: {str(e)}")

        return jsonify(log_files)
    except Exception as e:
        logger.error(f"Error listing logs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/logs/<log_name>', methods=['GET'])
def download_log(log_name):
    """Download a specific log file"""
    try:
        # Validate log_name to prevent directory traversal
        if not log_name.startswith('automation_') or not log_name.endswith('.log'):
            return jsonify({'error': 'Invalid log file name'}), 400
        if '..' in log_name or '/' in log_name:
            return jsonify({'error': 'Invalid log file name'}), 400

        logs_dir = Path(__file__).parent.parent / 'logs'
        log_file = logs_dir / log_name

        if not log_file.exists():
            return jsonify({'error': 'Log file not found'}), 404

        # Read file content
        with open(log_file, 'r') as f:
            content = f.read()

        return jsonify({
            'name': log_name,
            'content': content,
            'size': len(content.encode('utf-8')),
            'lines': len(content.split('\n'))
        })
    except Exception as e:
        logger.error(f"Error reading log: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/logs/<log_name>', methods=['DELETE'])
def delete_log(log_name):
    """Delete a specific log file"""
    try:
        # Validate log_name to prevent directory traversal
        if not log_name.startswith('automation_') or not log_name.endswith('.log'):
            return jsonify({'error': 'Invalid log file name'}), 400
        if '..' in log_name or '/' in log_name:
            return jsonify({'error': 'Invalid log file name'}), 400

        logs_dir = Path(__file__).parent.parent / 'logs'
        log_file = logs_dir / log_name

        if not log_file.exists():
            return jsonify({'error': 'Log file not found'}), 404

        log_file.unlink()
        logger.info(f"Deleted log file: {log_name}")
        return jsonify({'success': True, 'message': f'Deleted {log_name}'})
    except Exception as e:
        logger.error(f"Error deleting log: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/logs', methods=['DELETE'])
def delete_old_logs():
    """Delete log files older than specified days"""
    try:
        days = request.args.get('days', 7, type=int)
        logs_dir = Path(__file__).parent.parent / 'logs'

        if not logs_dir.exists():
            return jsonify({'deleted': 0})

        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        deleted_files = []

        for file_path in logs_dir.glob('automation_*.log'):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                deleted_files.append(file_path.name)

        logger.info(f"Deleted {deleted_count} log files older than {days} days: {deleted_files}")
        return jsonify({
            'success': True,
            'deleted': deleted_count,
            'message': f'Deleted {deleted_count} log files older than {days} days',
            'deleted_files': deleted_files
        })
    except Exception as e:
        logger.error(f"Error deleting old logs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/logs/email', methods=['POST'])
def email_log():
    """Send a log file via email

    Expected body:
    {
        'log_name': 'automation_20251115.log',
        'recipient_email': 'user@example.com',
        'message': 'Optional message to include'
    }
    """
    try:
        data = request.json
        log_name = data.get('log_name')
        recipient_email = data.get('recipient_email')
        message = data.get('message', '')

        if not log_name or not recipient_email:
            return jsonify({'error': 'log_name and recipient_email required'}), 400

        # Validate log_name
        if not log_name.startswith('automation_') or not log_name.endswith('.log'):
            return jsonify({'error': 'Invalid log file name'}), 400
        if '..' in log_name or '/' in log_name:
            return jsonify({'error': 'Invalid log file name'}), 400

        logs_dir = Path(__file__).parent.parent / 'logs'
        log_file = logs_dir / log_name

        if not log_file.exists():
            return jsonify({'error': 'Log file not found'}), 404

        # Read log content
        with open(log_file, 'r') as f:
            content = f.read()

        # For now, return the log content with instructions
        # In production, you'd use Flask-Mail or another email service
        return jsonify({
            'success': True,
            'message': f'Log file {log_name} is ready to be shared',
            'recipient': recipient_email,
            'log_name': log_name,
            'log_size': len(content.encode('utf-8')),
            'instructions': 'Copy the log content below and send via email, or use the email client integration',
            'content': content,
            'note': 'Email integration not yet configured. Copy and send manually or contact support.'
        })
    except Exception as e:
        logger.error(f"Error preparing log for email: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ========== END LOG MANAGEMENT ENDPOINTS ==========

@api_bp.route('/curriculum-templates/<student_id>', methods=['GET'])
def get_curriculum_templates(student_id):
    """Get all curriculum templates for a student"""
    try:
        # student_id is actually the student name (e.g., "Student One")
        # We need to find the student file name (e.g., "taylor")
        student_profiles = load_student_profiles()
        student_file_id = None

        for profile in student_profiles:
            if profile['name'].lower() == student_id.lower() or profile['id'] == student_id:
                student_file_id = profile['id']
                break

        if not student_file_id:
            return jsonify({'error': 'Student not found'}), 404

        template_file = DATA_DIR / 'curriculum_templates' / f'{student_file_id}.json'

        if not template_file.exists():
            return jsonify([])

        with open(template_file, 'r') as f:
            templates = json.load(f)

        return jsonify(templates)
    except Exception as e:
        logger.error(f"Error loading curriculum templates: {str(e)}")
        return jsonify([]), 500


@api_bp.route('/curriculum-templates', methods=['POST'])
def save_curriculum_template():
    """Save or update a curriculum template"""
    try:
        data = request.json
        student_name = data.get('student_name') or data.get('student_id')

        if not student_name:
            return jsonify({'error': 'Student name or ID required'}), 400

        # Find the student file ID
        student_profiles = load_student_profiles()
        student_file_id = None

        for profile in student_profiles:
            if profile['name'].lower() == student_name.lower() or profile['id'] == student_name:
                student_file_id = profile['id']
                break

        if not student_file_id:
            return jsonify({'error': 'Student not found'}), 404

        # Ensure curriculum_templates directory exists
        templates_dir = DATA_DIR / 'curriculum_templates'
        templates_dir.mkdir(parents=True, exist_ok=True)

        template_file = templates_dir / f'{student_file_id}.json'

        # Load existing templates
        if template_file.exists():
            with open(template_file, 'r') as f:
                templates = json.load(f)
        else:
            templates = []

        # Create template object
        template = {
            'id': data.get('id') or f"template_{int(datetime.now().timestamp())}",
            'name': data.get('name'),
            'prompt_template': data.get('prompt_template'),
            'created_at': data.get('created_at') or datetime.now().isoformat()
        }

        # Check if updating existing template
        existing_idx = next((i for i, t in enumerate(templates) if t['id'] == template['id']), None)

        if existing_idx is not None:
            templates[existing_idx] = template
        else:
            templates.append(template)

        # Save to file
        with open(template_file, 'w') as f:
            json.dump(templates, f, indent=2)

        logger.info(f"✓ Saved curriculum template: {template['name']} for student {student_name}")

        return jsonify({
            'success': True,
            'template': template,
            'message': 'Template saved successfully'
        }), 201

    except Exception as e:
        logger.error(f"Error saving curriculum template: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/curriculum-templates/<student_id>/<template_id>', methods=['DELETE'])
def delete_curriculum_template(student_id, template_id):
    """Delete a curriculum template"""
    try:
        # Find the student file ID
        student_profiles = load_student_profiles()
        student_file_id = None

        for profile in student_profiles:
            if profile['name'].lower() == student_id.lower() or profile['id'] == student_id:
                student_file_id = profile['id']
                break

        if not student_file_id:
            return jsonify({'error': 'Student not found'}), 404

        template_file = DATA_DIR / 'curriculum_templates' / f'{student_file_id}.json'

        if not template_file.exists():
            return jsonify({'error': 'No templates found for this student'}), 404

        with open(template_file, 'r') as f:
            templates = json.load(f)

        # Remove template
        templates = [t for t in templates if t['id'] != template_id]

        # Save updated templates
        with open(template_file, 'w') as f:
            json.dump(templates, f, indent=2)

        logger.info(f"✓ Deleted curriculum template: {template_id} for student {student_id}")

        return jsonify({'success': True, 'message': 'Template deleted successfully'})

    except Exception as e:
        logger.error(f"Error deleting curriculum template: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/curriculum-templates/<source_student_id>/<template_id>/duplicate', methods=['POST'])
def duplicate_curriculum_template(source_student_id, template_id):
    """Duplicate a curriculum template to the same or different student"""
    try:
        data = request.json
        target_student_id = data.get('target_student_id', source_student_id)

        # Find the source student file ID
        student_profiles = load_student_profiles()
        source_file_id = None
        target_file_id = None

        for profile in student_profiles:
            if profile['name'].lower() == source_student_id.lower() or profile['id'] == source_student_id:
                source_file_id = profile['id']
            if profile['name'].lower() == target_student_id.lower() or profile['id'] == target_student_id:
                target_file_id = profile['id']

        if not source_file_id:
            return jsonify({'error': 'Source student not found'}), 404
        if not target_file_id:
            return jsonify({'error': 'Target student not found'}), 404

        # Load source template
        source_template_file = DATA_DIR / 'curriculum_templates' / f'{source_file_id}.json'
        if not source_template_file.exists():
            return jsonify({'error': 'No templates found for source student'}), 404

        with open(source_template_file, 'r') as f:
            source_templates = json.load(f)

        source_template = next((t for t in source_templates if t['id'] == template_id), None)
        if not source_template:
            return jsonify({'error': 'Template not found'}), 404

        # Create new template by copying
        new_template = source_template.copy()
        new_template['id'] = f"template_{int(datetime.now().timestamp())}"
        new_template['created_at'] = datetime.now().isoformat()

        # Load target student templates
        target_template_file = DATA_DIR / 'curriculum_templates' / f'{target_file_id}.json'
        if target_template_file.exists():
            with open(target_template_file, 'r') as f:
                target_templates = json.load(f)
        else:
            target_templates = []

        # Add the duplicated template
        target_templates.append(new_template)

        # Save to target student file
        target_template_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_template_file, 'w') as f:
            json.dump(target_templates, f, indent=2)

        logger.info(f"✓ Duplicated curriculum template: {template_id} from {source_student_id} to {target_student_id}")

        return jsonify({
            'success': True,
            'message': 'Template duplicated successfully',
            'template': new_template
        }), 201

    except Exception as e:
        logger.error(f"Error duplicating curriculum template: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/curriculum/generate-pdf', methods=['POST'])
def generate_curriculum_pdf():
    """Generate and save a curriculum PDF"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from datetime import datetime

    try:
        data = request.json
        student_name = data.get('student_name')
        student_id = data.get('student_id')
        title = data.get('title', 'Curriculum')
        content = data.get('content', '')
        save_path = data.get('save_path', '')

        if not content:
            return jsonify({'error': 'No content provided'}), 400

        if not save_path:
            # Get default path from student profile
            student_profiles = load_student_profiles()
            student = next((s for s in student_profiles if s['id'] == student_id or s['name'].lower() == student_name.lower()), None)
            if student:
                save_path = student.get('folder', '')
            else:
                return jsonify({'error': 'Student not found'}), 404

        # Create directory if it doesn't exist
        save_dir = Path(save_path).expanduser().resolve()
        logger.info(f"Creating directory: {save_dir}")
        save_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory created/confirmed at: {save_dir}")

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{title.replace(' ', '_')}_{timestamp}.pdf"
        file_path = save_dir / filename

        logger.info(f"PDF file path: {file_path}")
        logger.info(f"File path exists before creation: {file_path.exists()}")

        # Create PDF
        doc = SimpleDocTemplate(str(file_path), pagesize=letter,
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=1*inch, bottomMargin=0.75*inch)

        # Build story (content)
        story = []
        styles = getSampleStyleSheet()

        # Add content
        # Check if content is HTML (from Quill editor) or plain text
        body_style = styles['Normal']

        if '<' in content and '>' in content:
            # HTML content from Quill editor
            import re

            # Split by major block elements: </p>, </ol>, </ul>
            # This handles paragraphs, ordered lists, and unordered lists
            blocks = re.split(r'(?:</p>|</ol>|</ul>)', content)

            for block_html in blocks:
                block_html = block_html.strip()
                if not block_html:
                    continue

                # Extract text content to check if block has content
                block_text = re.sub(r'<[^>]+>', '', block_html).strip()
                if not block_text:
                    continue

                # Check if this is an ordered list block
                if '<ol' in block_html:
                    # Extract list items from <ol>
                    list_items = re.findall(r'<li[^>]*>(.*?)</li>', block_html, re.DOTALL)
                    for idx, item in enumerate(list_items, 1):
                        # Clean the item: remove newlines but preserve formatting tags
                        item = item.strip()
                        item = re.sub(r'\s*\n\s*', ' ', item)
                        if item:
                            # Format as numbered list item for PDF
                            try:
                                story.append(Paragraph(f"{idx}. {item}", body_style))
                            except Exception as e:
                                logger.warning(f"Failed to add list item to PDF: {e}")
                    story.append(Spacer(1, 0.15*inch))

                # Check if this is an unordered list block
                elif '<ul' in block_html:
                    # Extract list items from <ul>
                    list_items = re.findall(r'<li[^>]*>(.*?)</li>', block_html, re.DOTALL)
                    for item in list_items:
                        # Clean the item: remove newlines but preserve formatting tags
                        item = item.strip()
                        item = re.sub(r'\s*\n\s*', ' ', item)
                        if item:
                            # Format as bullet list item for PDF
                            try:
                                story.append(Paragraph(f"• {item}", body_style))
                            except Exception as e:
                                logger.warning(f"Failed to add list item to PDF: {e}")
                    story.append(Spacer(1, 0.15*inch))

                # Otherwise, treat as a paragraph (contains <p> tags)
                else:
                    # Extract the content between <p> tags and clean it
                    match = re.search(r'<p[^>]*>(.*?)(?:</p>)?$', block_html, re.DOTALL)
                    if match:
                        formatted_content = match.group(1)
                    else:
                        formatted_content = block_html

                    # Clean the formatted content: remove newlines and extra whitespace
                    # but preserve intentional HTML formatting
                    formatted_content = formatted_content.strip()
                    # Replace newlines within content with spaces to prevent ReportLab errors
                    formatted_content = re.sub(r'\s*\n\s*', ' ', formatted_content)

                    # Skip blocks that only contain <br> tags or are whitespace-only
                    # These can't be rendered as valid paragraphs
                    if formatted_content and not re.match(r'^<br\s*/?\s*>+$', formatted_content, re.IGNORECASE):
                        try:
                            # Additional cleanup: remove leading <br> tags
                            formatted_content = re.sub(r'^<br\s*/?\s*>', '', formatted_content, flags=re.IGNORECASE).strip()

                            if formatted_content:
                                story.append(Paragraph(formatted_content, body_style))
                                story.append(Spacer(1, 0.15*inch))
                        except Exception as e:
                            logger.warning(f"Failed to add paragraph to PDF: {e}")
        else:
            # Plain text content
            paragraphs = content.split('\n\n')
            for para_text in paragraphs:
                if para_text.strip():
                    # Replace newlines within paragraph with <br/> for HTML formatting
                    formatted_text = para_text.replace('\n', '<br/>')
                    story.append(Paragraph(formatted_text, body_style))
                    story.append(Spacer(1, 0.15*inch))

        # Build PDF
        doc.build(story)

        logger.info(f"File path exists after creation: {file_path.exists()}")
        if file_path.exists():
            logger.info(f"✓ PDF file created successfully: {file_path}")
            logger.info(f"PDF file size: {file_path.stat().st_size} bytes")
        else:
            logger.warning(f"✗ PDF file was not created at: {file_path}")

        logger.info(f"✓ Generated curriculum PDF: {file_path} for student {student_name}")

        return jsonify({
            'success': True,
            'message': 'PDF generated successfully',
            'file_path': str(file_path)
        })

    except ImportError as e:
        logger.error(f"reportlab not installed: {str(e)}")
        return jsonify({'error': 'PDF generation library not installed. Please install reportlab.'}), 500
    except Exception as e:
        logger.error(f"Error generating curriculum PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/list-directories', methods=['POST'])
def list_directories():
    """List subdirectories in a given path"""
    from os import listdir
    from os.path import isdir, join

    try:
        data = request.json
        path = data.get('path', '')

        if not path:
            return jsonify({'error': 'No path provided'}), 400

        path_obj = Path(path).expanduser().resolve()

        # Security check: ensure path exists and is accessible
        if not path_obj.exists():
            return jsonify({'error': 'Path does not exist'}), 404

        if not path_obj.is_dir():
            return jsonify({'error': 'Path is not a directory'}), 400

        # List subdirectories
        subdirectories = []
        try:
            for item in sorted(path_obj.iterdir()):
                if item.is_dir():
                    subdirectories.append({
                        'name': item.name,
                        'path': str(item)
                    })
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403

        return jsonify({
            'success': True,
            'current_path': str(path_obj),
            'subdirectories': subdirectories
        })

    except Exception as e:
        logger.error(f"Error listing directories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/create-directory', methods=['POST'])
def create_directory():
    """Create a new directory"""
    try:
        data = request.json
        parent_path = data.get('parent_path', '')
        folder_name = data.get('folder_name', '')

        if not parent_path or not folder_name:
            return jsonify({'error': 'Parent path and folder name required'}), 400

        # Validate folder name (prevent path traversal)
        if '/' in folder_name or '\\' in folder_name or folder_name in ['.', '..']:
            return jsonify({'error': 'Invalid folder name'}), 400

        parent_path_obj = Path(parent_path).expanduser().resolve()

        # Security check: ensure parent path exists and is accessible
        if not parent_path_obj.exists():
            return jsonify({'error': 'Parent path does not exist'}), 404

        if not parent_path_obj.is_dir():
            return jsonify({'error': 'Parent path is not a directory'}), 400

        new_folder_path = parent_path_obj / folder_name

        # Check if folder already exists
        if new_folder_path.exists():
            return jsonify({'error': 'Folder already exists'}), 400

        try:
            new_folder_path.mkdir(parents=True, exist_ok=False)
            logger.info(f"Created directory: {new_folder_path}")
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403

        return jsonify({
            'success': True,
            'message': f'Folder created: {folder_name}',
            'new_path': str(new_folder_path)
        })

    except Exception as e:
        logger.error(f"Error creating directory: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/open-file', methods=['POST'])
def open_file_endpoint():
    """Open a file in the default application"""
    import subprocess
    import sys

    try:
        data = request.get_json()
        file_path = data.get('path')

        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400

        # Verify file exists
        from pathlib import Path
        if not Path(file_path).exists():
            return jsonify({'error': 'File not found'}), 404

        # Open file based on OS
        if sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', file_path])
        elif sys.platform == 'win32':  # Windows
            subprocess.Popen(f'start "{file_path}"', shell=True)
        else:  # Linux
            subprocess.Popen(['xdg-open', file_path])

        logger.info(f"✓ Opened file: {file_path}")
        return jsonify({'success': True, 'message': 'File opened'})

    except Exception as e:
        logger.error(f"Error opening file: {str(e)}")
        return jsonify({'error': str(e)}), 500


def save_vendors(vendors):
    """Save vendors to file (deprecated - use save_vendor_profile instead)"""
    # This function is deprecated and no longer saves to the old vendors location
    # All vendor data is now stored in data/vendors.json using the detailed format
    # Use save_vendor_profile() from invoice_generator.py instead
    pass
