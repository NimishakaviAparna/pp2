"""Routes package initialization"""
from .auth import auth_bp
from .admin import admin_bp
from .student import student_bp
from .company import company_bp
from .api import api_bp

__all__ = ['auth_bp', 'admin_bp', 'student_bp', 'company_bp', 'api_bp']