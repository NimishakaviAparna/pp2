"""
Admin Routes
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from datetime import datetime
from functools import wraps

from backend.models import (
    db, User, Student, Company, PlacementDrive, Application, UserRole,
    ActivityLog, Notification
)
from .auth import token_required, role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@role_required('admin')
def admin_dashboard():
    """Admin Dashboard - DYNAMIC STATISTICS"""
    total_students = User.query.filter_by(role=UserRole.STUDENT).count()
    total_companies = User.query.filter_by(role=UserRole.COMPANY).count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    selected = Application.query.filter_by(status='selected').count()
    
    # Pending approvals
    pending_companies = Company.query.filter_by(approval_status='pending').limit(5).all()
    pending_drives = PlacementDrive.query.filter_by(status='pending').limit(5).all()
    
    return render_template('admin/dashboard.html',
                          stats={
                              'total_students': total_students,
                              'total_companies': total_companies,
                              'total_drives': total_drives,
                              'total_applications': total_applications,
                              'total_selected': selected
                          },
                          pending_companies=pending_companies,
                          pending_drives=pending_drives)


@admin_bp.route('/companies')
@role_required('admin')
def manage_companies():
    """View and Manage Companies"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    approval_status = request.args.get('status', 'all', type=str)
    
    query = Company.query.join(User)
    
    if search:
        query = query.filter(
            (Company.company_name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    if approval_status != 'all':
        query = query.filter(Company.approval_status == approval_status)
    
    companies = query.paginate(page=page, per_page=10)
    
    return render_template('admin/companies.html',
                          companies=companies.items,
                          pagination=companies,
                          search=search,
                          status=approval_status)


@admin_bp.route('/company/<int:company_id>/approve', methods=['POST'])
@role_required('admin')
def approve_company(company_id):
    """Approve Company Registration"""
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'approved'
    
    # Log activity
    log = ActivityLog(
        action='COMPANY_APPROVED',
        description=f'Company {company.company_name} approved',
        user_id=request.user_id
    )
    
    # Create notification
    notification = Notification(
        user_id=company.user_id,
        notification_type='alert',
        subject='Company Approved',
        message=f'Your company {company.company_name} has been approved. You can now create placement drives.'
    )
    
    db.session.add(log)
    db.session.add(notification)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'message': 'Company approved'}), 200
    flash('Company approved successfully', 'success')
    return redirect(url_for('admin.manage_companies'))


@admin_bp.route('/company/<int:company_id>/reject', methods=['POST'])
@role_required('admin')
def reject_company(company_id):
    """Reject Company Registration"""
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'rejected'
    
    # Log activity
    log = ActivityLog(
        action='COMPANY_REJECTED',
        description=f'Company {company.company_name} rejected',
        user_id=request.user_id
    )
    
    # Create notification
    notification = Notification(
        user_id=company.user_id,
        notification_type='alert',
        subject='Company Registration Rejected',
        message=f'Your company {company.company_name} registration has been rejected.'
    )
    
    db.session.add(log)
    db.session.add(notification)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'message': 'Company rejected'}), 200
    flash('Company rejected', 'success')
    return redirect(url_for('admin.manage_companies'))


@admin_bp.route('/company/<int:company_id>/blacklist', methods=['POST'])
@role_required('admin')
def blacklist_company(company_id):
    """Blacklist Company"""
    company = Company.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    company.user.is_active = not company.is_blacklisted
    
    status = 'blacklisted' if company.is_blacklisted else 'unblacklisted'
    
    log = ActivityLog(
        action=f'COMPANY_{status.upper()}',
        description=f'Company {company.company_name} {status}',
        user_id=request.user_id
    )
    
    db.session.add(log)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'message': f'Company {status}'}), 200
    flash(f'Company {status}', 'success')
    return redirect(url_for('admin.manage_companies'))


@admin_bp.route('/drives')
@role_required('admin')
def manage_drives():
    """View and Manage Placement Drives"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all', type=str)
    
    query = PlacementDrive.query
    
    if status != 'all':
        query = query.filter(PlacementDrive.status == status)
    
    drives = query.paginate(page=page, per_page=10)
    
    return render_template('admin/drives.html',
                          drives=drives.items,
                          pagination=drives,
                          status=status)


@admin_bp.route('/drive/<int:drive_id>/approve', methods=['POST'])
@role_required('admin')
def approve_drive(drive_id):
    """Approve Placement Drive"""
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'approved'
    
    log = ActivityLog(
        action='DRIVE_APPROVED',
        description=f'Drive {drive.job_title} approved',
        user_id=request.user_id
    )
    
    notification = Notification(
        user_id=drive.company.user_id,
        notification_type='alert',
        subject='Placement Drive Approved',
        message=f'Your placement drive for {drive.job_title} has been approved.'
    )
    
    db.session.add(log)
    db.session.add(notification)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'message': 'Drive approved'}), 200
    flash('Drive approved', 'success')
    return redirect(url_for('admin.manage_drives'))


@admin_bp.route('/drive/<int:drive_id>/reject', methods=['POST'])
@role_required('admin')
def reject_drive(drive_id):
    """Reject Placement Drive"""
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'rejected'
    
    log = ActivityLog(
        action='DRIVE_REJECTED',
        description=f'Drive {drive.job_title} rejected',
        user_id=request.user_id
    )
    
    notification = Notification(
        user_id=drive.company.user_id,
        notification_type='alert',
        subject='Placement Drive Rejected',
        message=f'Your placement drive for {drive.job_title} has been rejected.'
    )
    
    db.session.add(log)
    db.session.add(notification)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'message': 'Drive rejected'}), 200
    flash('Drive rejected', 'success')
    return redirect(url_for('admin.manage_drives'))


@admin_bp.route('/students')
@role_required('admin')
def manage_students():
    """View Students"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Student.query.join(User)
    
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (Student.branch.ilike(f'%{search}%'))
        )
    
    students = query.paginate(page=page, per_page=10)
    
    return render_template('admin/students.html',
                          students=students.items,
                          pagination=students,
                          search=search)


@admin_bp.route('/student/<int:student_id>/blacklist', methods=['POST'])
@role_required('admin')
def blacklist_student(student_id):
    """Blacklist/Unblacklist Student"""
    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = not student.is_blacklisted
    student.user.is_active = not student.is_blacklisted
    
    status = 'blacklisted' if student.is_blacklisted else 'unblacklisted'
    
    log = ActivityLog(
        action=f'STUDENT_{status.upper()}',
        description=f'Student {student.user.name} {status}',
        user_id=request.user_id
    )
    
    db.session.add(log)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'message': f'Student {status}'}), 200
    flash(f'Student {status}', 'success')
    return redirect(url_for('admin.manage_students'))


@admin_bp.route('/reports')
@role_required('admin')
def view_reports():
    """View Placement Reports"""
    from backend.models import MonthlyReport
    
    total_students = User.query.filter_by(role=UserRole.STUDENT).count()
    total_applications = Application.query.count()
    selected = Application.query.filter_by(status='selected').count()
    placement_percentage = (selected / total_applications * 100) if total_applications > 0 else 0
    
    # Get latest monthly reports
    monthly_reports = MonthlyReport.query.order_by(MonthlyReport.month.desc()).limit(12).all()
    
    return render_template('admin/reports.html',
                          stats={
                              'total_students': total_students,
                              'total_applications': total_applications,
                              'total_selected': selected,
                              'placement_percentage': f'{placement_percentage:.1f}%'
                          },
                          monthly_reports=monthly_reports)