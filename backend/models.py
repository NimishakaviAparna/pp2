"""
Database Models for Placement Portal
"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

db = SQLAlchemy()


class UserRole(enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    STUDENT = "student"
    COMPANY = "company"


class User(db.Model):
    """Unified User Model for all roles"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    company_profile = db.relationship('Company', backref='user', uselist=False, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<User {self.email} - {self.role.value}>'


class Student(db.Model):
    """Student Profile Model"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Academic Details
    branch = db.Column(db.String(100), nullable=False, default='')
    year = db.Column(db.String(50), nullable=False, default='')
    cgpa = db.Column(db.Float, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    # Resume
    resume_filename = db.Column(db.String(255), nullable=True)
    resume_path = db.Column(db.String(500), nullable=True)
    
    # Status
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.user.name,
            'email': self.user.email,
            'branch': self.branch,
            'year': self.year,
            'cgpa': self.cgpa,
            'phone': self.phone,
            'address': self.address,
            'resume_filename': self.resume_filename,
            'is_blacklisted': self.is_blacklisted
        }
    
    def __repr__(self):
        return f'<Student {self.user.name} - {self.branch}>'


class Company(db.Model):
    """Company Profile Model"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Company Details
    company_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100), nullable=False, default='')
    location = db.Column(db.String(200), nullable=False, default='')
    website = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Approval Status
    approval_status = db.Column(db.String(20), default='pending')
    logo_filename = db.Column(db.String(255), nullable=True)
    
    # Status
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    placement_drives = db.relationship('PlacementDrive', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'email': self.user.email,
            'industry': self.industry,
            'location': self.location,
            'website': self.website,
            'phone': self.phone,
            'description': self.description,
            'approval_status': self.approval_status,
            'is_blacklisted': self.is_blacklisted
        }
    
    def __repr__(self):
        return f'<Company {self.company_name}>'


class PlacementDrive(db.Model):
    """Placement Drive Model"""
    __tablename__ = 'placement_drives'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Drive Details
    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    
    # Eligibility
    min_cgpa = db.Column(db.Float, nullable=True)
    eligible_branches = db.Column(db.String(500), nullable=True)
    eligible_years = db.Column(db.String(255), nullable=True)
    
    # Compensation
    salary_min = db.Column(db.Float, nullable=False)
    salary_max = db.Column(db.Float, nullable=False)
    
    # Timeline
    application_deadline = db.Column(db.DateTime, nullable=False)
    interview_start_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status: pending, approved, closed, rejected
    status = db.Column(db.String(20), default='pending')
    
    # Relationships
    applications = db.relationship('Application', backref='drive', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'company_name': self.company.company_name,
            'job_title': self.job_title,
            'job_description': self.job_description,
            'location': self.location,
            'job_type': self.job_type,
            'min_cgpa': self.min_cgpa,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'application_deadline': self.application_deadline.isoformat(),
            'status': self.status,
            'applications_count': len(self.applications)
        }
    
    def is_deadline_passed(self):
        """Check if application deadline has passed"""
        return datetime.utcnow() > self.application_deadline
    
    def __repr__(self):
        return f'<Drive {self.job_title} @ {self.company.company_name}>'


class Application(db.Model):
    """Student Application Model"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=False)
    
    # Application Status
    status = db.Column(db.String(20), default='applied')
    
    # Dates
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional Info
    cover_letter = db.Column(db.Text, nullable=True)
    interview_date = db.Column(db.DateTime, nullable=True)
    interview_round = db.Column(db.Integer, default=0)
    interview_feedback = db.Column(db.Text, nullable=True)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive'),)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_name': self.student.user.name,
            'student_email': self.student.user.email,
            'drive_id': self.drive_id,
            'job_title': self.drive.job_title,
            'company_name': self.drive.company.company_name,
            'status': self.status,
            'applied_at': self.applied_at.isoformat(),
            'interview_date': self.interview_date.isoformat() if self.interview_date else None,
            'interview_round': self.interview_round
        }
    
    def __repr__(self):
        return f'<Application {self.student.user.name} -> {self.drive.job_title}>'


class ActivityLog(db.Model):
    """Activity Log for Admin Reporting"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ActivityLog {self.action}>'


class MonthlyReport(db.Model):
    """Monthly Placement Report"""
    __tablename__ = 'monthly_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(10), nullable=False, unique=True)
    total_drives = db.Column(db.Integer, default=0)
    total_applications = db.Column(db.Integer, default=0)
    total_selected = db.Column(db.Integer, default=0)
    report_html = db.Column(db.Text, nullable=True)
    report_data = db.Column(db.JSON, nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_to_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<MonthlyReport {self.month}>'


class Notification(db.Model):
    """Notification Model for reminders and alerts"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.subject}>'