"""
app.py
Application entry point. Creates and configures the Flask app,
registers blueprints, sets up logging, and seeds the default admin user.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, session, send_from_directory
from flask_wtf import CSRFProtect

from config import config_map
from models import db
from models.user import User


def create_app(config_name=None):
    """Application factory."""
    app = Flask(__name__)

    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)

    # Extensions
    db.init_app(app)
    csrf = CSRFProtect(app)

    # Blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.employee import employee_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(employee_bp)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    if not app.debug:
        handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=1_000_000, backupCount=3)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

    # ------------------------------------------------------------------
    # Serve uploaded profile images
    # ------------------------------------------------------------------
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # ------------------------------------------------------------------
    # Context processor: expose logged-in user info to all templates
    # ------------------------------------------------------------------
    @app.context_processor
    def inject_user():
        return {
            'current_user_name': session.get('name'),
            'current_user_role': session.get('role'),
            'current_user_image': session.get('profile_image'),
        }

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('error.html', code=403, message='Forbidden: You do not have access to this resource.'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', code=404, message='Page not found.'), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template('error.html', code=413, message='Uploaded file is too large (max 2MB).'), 413

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f'Server error: {e}')
        return render_template('error.html', code=500, message='Internal server error. Please try again later.'), 500

    # ------------------------------------------------------------------
    # Security headers
    # ------------------------------------------------------------------
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # ------------------------------------------------------------------
    # Seed default admin account on first run
    # ------------------------------------------------------------------
    with app.app_context():
        db.create_all()
        seed_default_admin(app)

    return app


def seed_default_admin(app):
    """Create the default admin account if it doesn't already exist."""
    admin_email = app.config['DEFAULT_ADMIN_EMAIL']
    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        return

    admin = User(
        name='System Administrator',
        email=admin_email,
        phone='0000000000',
        department='Administration',
        designation='Administrator',
        role='admin',
        profile_image='default.png',
        status='active',
    )
    admin.set_password(app.config['DEFAULT_ADMIN_PASSWORD'])
    db.session.add(admin)
    db.session.commit()
    app.logger.info(f'Seeded default admin account: {admin_email}')


app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
