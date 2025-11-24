"""Utility functions for ESA Helper application"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / 'data'


def load_config():
    """Load configuration from config.json"""
    config_file = Path(__file__).parent.parent / 'config.json'
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return None


def save_config(config):
    """Save configuration to config.json"""
    config_file = Path(__file__).parent.parent / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def load_templates():
    """Load all templates from data/esa_templates directory"""
    templates_dir = DATA_DIR / 'esa_templates'
    templates_dir.mkdir(parents=True, exist_ok=True)

    templates = []
    for template_file in templates_dir.glob('*.json'):
        try:
            with open(template_file, 'r') as f:
                data = json.load(f)
                # Each file contains an array of templates
                if isinstance(data, list):
                    templates.extend(data)
                else:
                    # Support old format (single template object)
                    templates.append(data)
        except Exception as e:
            logging.warning(f"Error loading template file {template_file}: {str(e)}")

    return templates


def load_student_templates(student_id: str):
    """Load templates for a specific student by ID"""
    templates_dir = DATA_DIR / 'esa_templates'
    template_file = templates_dir / f'{student_id}.json'

    if not template_file.exists():
        # Templates are optional - return empty list if not found
        return []

    try:
        with open(template_file, 'r') as f:
            data = json.load(f)
            # File should contain an array of templates
            if isinstance(data, list):
                return data
            else:
                # Support old format (single template object)
                return [data]
    except Exception as e:
        logging.error(f"Error loading templates for student {student_id}: {str(e)}")
        return []


def load_template(template_id):
    """Load specific template by ID"""
    templates_dir = DATA_DIR / 'esa_templates'
    template_file = templates_dir / f'{template_id}.json'

    if template_file.exists():
        with open(template_file, 'r') as f:
            return json.load(f)
    return None


def save_template(template):
    """Save template to file"""
    templates_dir = DATA_DIR / 'esa_templates'
    templates_dir.mkdir(parents=True, exist_ok=True)

    template_id = template.get('id', template.get('name').lower().replace(' ', '_'))
    template_file = templates_dir / f'{template_id}.json'

    with open(template_file, 'w') as f:
        json.dump(template, f, indent=2)

    return template_id


def save_student_template(template, student_id):
    """Save template for a specific student (new format using student_id as file key)"""
    templates_dir = DATA_DIR / 'esa_templates'
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Generate ID if not provided
    if not template.get('id'):
        template['id'] = template.get('name', 'template').lower().replace(' ', '_') + '_' + datetime.now().strftime('%Y%m%d%H%M%S')

    # Load existing templates for this student
    template_file = templates_dir / f'{student_id}.json'
    templates = load_student_templates(student_id)

    # Update or add template
    existing_idx = next((i for i, t in enumerate(templates) if t.get('id') == template['id']), -1)
    if existing_idx >= 0:
        templates[existing_idx] = template
    else:
        templates.append(template)

    # Save all templates for this student
    with open(template_file, 'w') as f:
        json.dump(templates, f, indent=2)

    return template['id']


def delete_student_template(student_id, template_id):
    """Delete template for a specific student"""
    templates_dir = DATA_DIR / 'esa_templates'
    template_file = templates_dir / f'{student_id}.json'

    if not template_file.exists():
        return False

    templates = load_student_templates(student_id)
    original_count = len(templates)

    # Filter out the template to delete
    templates = [t for t in templates if t.get('id') != template_id]

    # If nothing was deleted, return False
    if len(templates) == original_count:
        return False

    # Save updated templates
    with open(template_file, 'w') as f:
        json.dump(templates, f, indent=2)

    return True


def load_vendors():
    """Load basic vendor list from data/vendors.json (deprecated - use load_vendor_profiles instead)"""
    # This function is kept for backward compatibility but is deprecated
    # All new code should use load_vendor_profiles() from invoice_generator.py instead
    from app.invoice_generator import load_vendor_profiles
    vendors = load_vendor_profiles()
    # Return simplified format for backward compatibility, but include classwallet_search_term for Direct Pay
    return [{'id': v['id'], 'name': v['name'], 'location': '', 'classwallet_search_term': v.get('classwallet_search_term', '')} for v in vendors]


def save_vendors(vendors):
    """Save vendors to file (deprecated - use save_vendor_profile instead)"""
    # This function is kept for backward compatibility but is deprecated
    # All new code should use save_vendor_profile() from invoice_generator.py instead
    pass


def generate_po_number():
    """Generate PO number in format YYYYMMDD_hhmm"""
    return datetime.now().strftime('%Y%m%d_%H%M')


def get_student_path(student):
    """Get base folder path for student

    Note: This is a fallback that constructs paths from the student_id.
    User should configure student folder paths in the student profile.
    """
    # This function is primarily for backward compatibility
    # New implementations should use the folder path from student profiles
    base = '/path/to/esa/documents'
    current_year = datetime.now().year

    # Generic path construction - actual paths should come from student profile
    return f'{base}/{student.lower()}/{current_year}'


def log_submission(submission_data, created_by='production'):
    """
    Log submission to file and update master history

    Args:
        submission_data: Dictionary with submission details
        created_by: Source of submission - 'production', 'test', or other identifier
    """
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"submission_{timestamp}.json"

    # Add metadata
    submission_data['logged_at'] = datetime.now().isoformat()
    submission_data['timestamp'] = timestamp
    submission_data['created_by'] = created_by

    with open(log_file, 'w') as f:
        json.dump(submission_data, f, indent=2)

    # Update master history file
    _update_submission_history(submission_data)

    return log_file


def _update_submission_history(submission_data):
    """
    Update the master submission history file

    Args:
        submission_data: Dictionary with submission details to add to history
    """
    log_dir = Path(__file__).parent.parent / 'logs'
    history_file = log_dir / 'submission_history.json'

    try:
        # Load existing history
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = {'submissions': []}

        # Ensure submissions key exists
        if 'submissions' not in history:
            history['submissions'] = []

        # Add new submission
        history['submissions'].append(submission_data)

        # Write back
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

    except Exception as e:
        logger.error(f"Error updating submission history: {str(e)}")


def get_submission_history():
    """
    Get all submissions from history file

    Returns:
        List of submission dictionaries, sorted by date (newest first)
    """
    log_dir = Path(__file__).parent.parent / 'logs'
    history_file = log_dir / 'submission_history.json'

    if not history_file.exists():
        return []

    try:
        with open(history_file, 'r') as f:
            data = json.load(f)
            submissions = data.get('submissions', [])
            # Sort by timestamp, newest first
            submissions.sort(key=lambda x: x.get('logged_at', ''), reverse=True)
            return submissions
    except Exception as e:
        logger.error(f"Error reading submission history: {str(e)}")
        return []


def delete_submission(timestamp):
    """
    Delete a submission from history by timestamp

    Args:
        timestamp: The timestamp of the submission to delete (e.g., '20251112_000140')

    Returns:
        bool: True if successful, False otherwise
    """
    log_dir = Path(__file__).parent.parent / 'logs'
    history_file = log_dir / 'submission_history.json'
    submission_file = log_dir / f'submission_{timestamp}.json'

    try:
        # Delete individual submission file if it exists
        if submission_file.exists():
            submission_file.unlink()
            logger.info(f"Deleted submission file: {submission_file}")

        # Update master history file
        if history_file.exists():
            with open(history_file, 'r') as f:
                data = json.load(f)

            # Remove submission with matching timestamp
            submissions = data.get('submissions', [])
            original_count = len(submissions)
            submissions = [s for s in submissions if s.get('timestamp') != timestamp]

            if len(submissions) < original_count:
                data['submissions'] = submissions
                with open(history_file, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Removed submission {timestamp} from history")
                return True
            else:
                logger.warning(f"Submission {timestamp} not found in history")
                return False
        else:
            logger.warning(f"History file not found: {history_file}")
            return False

    except Exception as e:
        logger.error(f"Error deleting submission {timestamp}: {str(e)}")
        return False


def delete_all_submissions(created_by_filter=None):
    """
    Delete submissions from history

    Args:
        created_by_filter: Only delete submissions with this created_by value.
                          If None, deletes all submissions.
                          Common values: 'test', 'production'

    Returns:
        dict: {'success': bool, 'deleted_count': int, 'message': str}
    """
    log_dir = Path(__file__).parent.parent / 'logs'
    history_file = log_dir / 'submission_history.json'

    try:
        deleted_count = 0

        # If filtering by created_by, read history first to identify which files to delete
        files_to_delete = []

        if created_by_filter:
            # Load history to find submissions with matching created_by
            if history_file.exists():
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    submissions = data.get('submissions', [])

                    # Find timestamps of submissions to delete
                    for submission in submissions:
                        if submission.get('created_by') == created_by_filter:
                            files_to_delete.append(submission.get('timestamp'))
        else:
            # No filter - delete all submission files
            if log_dir.exists():
                for file in log_dir.glob('submission_*.json'):
                    if file.name != 'submission_history.json':
                        # Extract timestamp from filename
                        timestamp = file.stem.replace('submission_', '')
                        files_to_delete.append(timestamp)

        # Delete individual submission files
        for timestamp in files_to_delete:
            try:
                file_path = log_dir / f'submission_{timestamp}.json'
                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted submission file: submission_{timestamp}.json")
            except Exception as e:
                logger.warning(f"Could not delete submission_{timestamp}.json: {str(e)}")

        # Update the master history file (remove deleted entries)
        if history_file.exists():
            with open(history_file, 'r') as f:
                data = json.load(f)
                submissions = data.get('submissions', [])

            if created_by_filter:
                # Keep only submissions that don't match the filter
                submissions = [s for s in submissions if s.get('created_by') != created_by_filter]
            else:
                # Clear all submissions
                submissions = []

            data['submissions'] = submissions
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)

        filter_text = f" with created_by='{created_by_filter}'" if created_by_filter else ""
        logger.info(f"Deleted {deleted_count} submission(s){filter_text}")
        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} submission(s){filter_text}'
        }

    except Exception as e:
        logger.error(f"Error deleting submissions: {str(e)}")
        return {
            'success': False,
            'deleted_count': 0,
            'message': f'Error: {str(e)}'
        }


def get_temp_upload_dir():
    """Get or create temporary upload directory"""
    temp_dir = DATA_DIR / 'temp_uploads'
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def split_pdf(pdf_path):
    """
    Split a multi-page PDF into individual single-page PDFs

    Args:
        pdf_path: Path to the PDF file to split

    Returns:
        List of tuples: [(output_filename, output_path), ...]
        or empty list if PDF has only 1 page
    """
    try:
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return []

        # Read the PDF
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)

        # If only 1 page, no need to split
        if num_pages <= 1:
            return []

        # Create temp directory for split files
        temp_dir = get_temp_upload_dir()

        # Generate base filename without extension
        base_name = pdf_path.stem

        split_files = []

        # Split into individual pages
        for page_num in range(num_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])

            # Create output filename with page number
            output_filename = f"{base_name}_{page_num + 1}.pdf"
            output_path = temp_dir / output_filename

            # Write the single-page PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            split_files.append({
                'filename': output_filename,
                'path': str(output_path),
                'page_num': page_num + 1,
                'total_pages': num_pages
            })

            logger.info(f"✓ Created split PDF: {output_filename}")

        return split_files

    except Exception as e:
        logger.error(f"Error splitting PDF {pdf_path}: {str(e)}")
        return []


def get_temp_files():
    """Get list of all temporary upload files"""
    temp_dir = get_temp_upload_dir()

    files = []
    for file_path in sorted(temp_dir.glob('*')):
        if file_path.is_file():
            files.append({
                'filename': file_path.name,
                'path': str(file_path),
                'size': file_path.stat().st_size,
                'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                'size_mb': round(file_path.stat().st_size / (1024 * 1024), 2)
            })

    return files


def delete_temp_file(filename):
    """Delete a temporary file"""
    temp_dir = get_temp_upload_dir()
    file_path = temp_dir / filename

    # Security: ensure the file is actually in the temp directory
    if file_path.parent != temp_dir:
        logger.error(f"Security: Attempted to delete file outside temp directory: {file_path}")
        return False

    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"✓ Deleted temp file: {filename}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting temp file {filename}: {str(e)}")
        return False


def cleanup_old_temp_files(days=7):
    """
    Clean up temporary files older than specified days

    Args:
        days: Delete files older than this many days (default 7)

    Returns:
        Number of files deleted
    """
    temp_dir = get_temp_upload_dir()
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

    deleted_count = 0
    for file_path in temp_dir.glob('*'):
        if file_path.is_file():
            if file_path.stat().st_ctime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"✓ Auto-deleted old temp file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Error auto-deleting {file_path.name}: {str(e)}")

    return deleted_count
