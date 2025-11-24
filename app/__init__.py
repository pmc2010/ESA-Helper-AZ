"""ESA Helper Flask Application"""

import os
from pathlib import Path
from flask import Flask


def create_app():
    """Application factory for Flask app"""
    # Get the directory where this file is located
    basedir = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(basedir, 'templates'),
        static_folder=os.path.join(basedir, 'static')
    )
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file upload

    # Initialize required directories for new users
    _initialize_directories(basedir)

    # Register blueprints
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app


def _initialize_directories(basedir):
    """
    Create required directories if they don't exist.
    Called during app initialization to ensure all necessary folders are available.
    """
    project_root = Path(basedir).parent

    directories_to_create = [
        project_root / 'data',
        project_root / 'data' / 'esa_templates',
        project_root / 'data' / 'curriculum_templates',
        project_root / 'data' / 'temp_uploads',
        project_root / 'logs',
    ]

    for directory in directories_to_create:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Log warning but don't fail - the app can still run if some dirs can't be created
            print(f"Warning: Could not create directory {directory}: {str(e)}")
