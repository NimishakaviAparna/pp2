"""
Main Flask Application
"""
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_caching import Cache
from dotenv import load_dotenv
import os
from functools import wraps

from config import config
from backend.models import db, User, UserRole
from backend.routes import auth_bp, admin_bp, student_bp, company_bp, api_bp
from backend.email_utils import mail
from backend.tasks import celery, init_celery

# Load environment variables
load_dotenv()

# Cache
cache = Cache(config={'CACHE_TYPE': 'simple'})


def create_app(config_name='development'):
    """
    Application Factory
    """
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Load Configuration
    app.config.from_object(config[config_name])
    
    # Initialize Extensions
    db.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    jwt = JWTManager(app)
    CORS(app)
    
    # Initialize Celery
    init_celery(app)
    
    # Create upload directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(api_bp)
    
    # Database initialization
    with app.app_context():
        db.create_all()
        
        # Create Admin if doesn't exist
        admin = User.query.filter_by(email='admin@placement.com', role=UserRole.ADMIN).first()
        if not admin:
            admin = User(
                name='Admin',
                email='admin@placement.com',
                role=UserRole.ADMIN,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✅ Admin user created: admin@placement.com / admin123')
    
    # Routes
    @app.route('/')
    def index():
        """Landing Page"""
        return render_template('index.html')
    
    @app.route('/student_dashboard')
    def student_dashboard():
        """Redirect to student dashboard"""
        return redirect(url_for('student.student_dashboard'))
    
    @app.route('/admin_dashboard')
    def admin_dashboard():
        """Redirect to admin dashboard"""
        return redirect(url_for('admin.admin_dashboard'))
    
    @app.route('/company_dashboard')
    def company_dashboard():
        """Redirect to company dashboard"""
        return redirect(url_for('company.company_dashboard'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors"""
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.context_processor
    def inject_user():
        """Inject user info in templates"""
        user_id = request.cookies.get('user_id')
        user_role = request.cookies.get('user_role')
        user_name = request.cookies.get('user_name')
        
        return {
            'current_user_id': user_id,
            'current_user_role': user_role,
            'current_user_name': user_name,
            'is_authenticated': bool(user_id)
        }
    
    return app


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, port=5000)