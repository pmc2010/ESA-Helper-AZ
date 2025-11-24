"""ESA Helper Flask Application"""

import os
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

    # Register blueprints
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
