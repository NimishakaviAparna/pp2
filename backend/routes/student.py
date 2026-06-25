"""
Student Routes
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_from_directory
from datetime import datetime
from functools import wraps
import os
from werkzeug.utils import secure_filename

from backend.models import (
    db, User, Student, PlacementDrive, Application, UserRole,
    ActivityLog, Notification
)
from config import Config
from .auth import token_required, role_required

student_bp = Blueprint('student', __name__, url_prefix='/student')


def get_student_from_token():
    """Get student object from JWT token"""
    user = User.query.get(request.user_id)
    if not user or user.role != UserRole.STUDENT:
        return None
    return user.student_profile


@student_bp.route('/dashboard')
@role_required('student')
def student_dashboard():
    """Student Dashboard"""
    student = get_student_from_token()
    if not student:
        flash('Student profile not found', 'error')
        return redirect(url_for('auth.login'))
    
    # Get Stats
    total_applications = Application.query.filter_by(student_id=student.id).count()
    shortlisted = Application.query.filter_by(
        student_id=student.id,
        status='shortlisted'
    ).count()
    selected = Application.query.filter_by(
        student_id=student.id,
        status='selected'
    ).count()
    
    # Get Approved Drives
    approved_drives = PlacementDrive.query.filter_by(status='approved').limit(10).all()
    
    # Get Recent Applications
    applications = Application.query.filter_by(student_id=student.id).order_by(
        Application.applied_at.desc()
    ).limit(5).all()
    
    return render_template('student/dashboard.html',
                          student=student,
                          stats={
                              'total_applications': total_applications,
                              'shortlisted': shortlisted,
                              'selected': selected
                          },
                          drives=approved_drives,
                          applications=applications)


@student_bp.route('/profile')
@role_required('student')
def student_profile():
    """View Student Profile"""
    student = get_student_from_token()
    if not student:
        flash('Student profile not found', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('student/profile.html', student=student)


@student_bp.route('/profile/edit', methods=['GET', 'POST'])
@role_required('student')
def edit_profile():
    """Edit Student Profile"""
    student = get_student_from_token()
    if not student:
        flash('Student profile not found', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Update fields
        student.branch = request.form.get('branch', student.branch)
        student.year = request.form.get('year', student.year)
        
        try:
            cgpa = float(request.form.get('cgpa', student.cgpa or 0))
            if 0 <= cgpa <= 10:
                student.cgpa = cgpa
        except ValueError:
            pass
        
        student.phone = request.form.get('phone', student.phone)
        student.address = request.form.get('address', student.address)
        
        # Handle resume upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename:
                filename = secure_filename(f'{student.id}_{datetime.utcnow().timestamp()}_{file.filename}')
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                student.resume_filename = file.filename
                student.resume_path = filepath
        
        db.session.commit()
        
        log = ActivityLog(
            action='PROFILE_UPDATED',
            description=f'Student {student.user.name} updated profile',
            user_id=request.user_id
        )
        db.session.add(log)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': 'Profile updated'}), 200
        flash('Profile updated successfully', 'success')
        return redirect(url_for('student.student_profile'))
    
    return render_template('student/edit_profile.html', student=student)


@student_bp.route('/drives')
@role_required('student')
def student_drives():
    """View All Approved Placement Drives"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    job_type = request.args.get('type', 'all', type=str)
    min_salary = request.args.get('salary_min', 0, type=float)
    
    query = PlacementDrive.query.filter_by(status='approved')
    
    if search:
        query = query.filter(
            (PlacementDrive.job_title.ilike(f'%{search}%')) |
            (PlacementDrive.location.ilike(f'%{search}%'))
        )
    
    if job_type != 'all':
        query = query.filter(PlacementDrive.job_type == job_type)
    
    if min_salary > 0:
        query = query.filter(PlacementDrive.salary_min >= min_salary)
    
    drives = query.order_by(PlacementDrive.application_deadline).paginate(page=page, per_page=10)
    
    return render_template('student/drives.html',
                          drives=drives.items,
                          pagination=drives,
                          search=search,
                          job_type=job_type,
                          min_salary=min_salary)


@student_bp.route('/drive/<int:drive_id>')
@role_required('student')
def view_drive(drive_id):
    """View Drive Details"""
    drive = PlacementDrive.query.get_or_404(drive_id)
    student = get_student_from_token()
    
    if not student:
        return redirect(url_for('auth.login'))
    
    # Check if student already applied
    has_applied = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first() is not None
    
    # Check eligibility
    eligible = True
    eligibility_reasons = []
    
    if drive.min_cgpa and student.cgpa:
        if student.cgpa < drive.min_cgpa:
            eligible = False
            eligibility_reasons.append(f'CGPA {student.cgpa} < {drive.min_cgpa}')
    
    if drive.eligible_branches:
        branches = [b.strip() for b in drive.eligible_branches.split(',')]
        if student.branch not in branches:
            eligible = False
            eligibility_reasons.append(f'Branch {student.branch} not eligible')
    
    if drive.eligible_years:
        years = [y.strip() for y in drive.eligible_years.split(',')]
        if student.year not in years:
            eligible = False
            eligibility_reasons.append(f'Year {student.year} not eligible')
    
    return render_template('student/drive_detail.html',
                          drive=drive,
                          has_applied=has_applied,
                          company=drive.company,
                          eligible=eligible,
                          eligibility_reasons=eligibility_reasons)


@student_bp.route('/apply/<int:drive_id>', methods=['POST'])
@role_required('student')
def apply_drive(drive_id):
    """Apply for a Drive"""
    drive = PlacementDrive.query.get_or_404(drive_id)
    student = get_student_from_token()
    
    if not student:
        return jsonify({'message': 'Student not found'}), 404
    
    # Check if deadline passed
    if drive.is_deadline_passed():
        msg = 'Application deadline has passed'
        if request.is_json:
            return jsonify({'message': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('student.view_drive', drive_id=drive_id))
    
    # Check if already applied
    existing = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first()
    
    if existing:
        msg = 'Already applied to this drive'
        if request.is_json:
            return jsonify({'message': msg}), 409
        flash(msg, 'warning')
        return redirect(url_for('student.view_drive', drive_id=drive_id))
    
    # Check eligibility
    if drive.min_cgpa and student.cgpa:
        if student.cgpa < drive.min_cgpa:
            msg = f'CGPA requirement not met (Required: {drive.min_cgpa})'
            if request.is_json:
                return jsonify({'message': msg}), 403
            flash(msg, 'error')
            return redirect(url_for('student.view_drive', drive_id=drive_id))
    
    try:
        # Create Application
        application = Application(
            student_id=student.id,
            drive_id=drive_id,
            status='applied',
            cover_letter=request.form.get('cover_letter') if request.method == 'POST' else None
        )
        db.session.add(application)
        
        # Log activity
        log = ActivityLog(
            action='APPLICATION_SUBMITTED',
            description=f'{student.user.name} applied for {drive.job_title}',
            user_id=request.user_id
        )
        db.session.add(log)
        
        # Create notification for company
        notification = Notification(
            user_id=drive.company.user_id,
            notification_type='alert',
            subject='New Application',
            message=f'{student.user.name} has applied for {drive.job_title}'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        msg = 'Applied successfully!'
        if request.is_json:
            return jsonify({'message': msg}), 201
        flash(msg, 'success')
        return redirect(url_for('student.student_applications'))
    
    except Exception as e:
        db.session.rollback()
        msg = f'Error: {str(e)}'
        if request.is_json:
            return jsonify({'message': msg}), 500
        flash(msg, 'error')
        return redirect(url_for('student.view_drive', drive_id=drive_id))


@student_bp.route('/applications')
@role_required('student')
def student_applications():
    """View All Student Applications"""
    student = get_student_from_token()
    if not student:
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all', type=str)
    
    query = Application.query.filter_by(student_id=student.id)
    
    if status != 'all':
        query = query.filter(Application.status == status)
    
    applications = query.order_by(Application.applied_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('student/applications.html',
                          applications=applications.items,
                          pagination=applications,
                          status=status)


@student_bp.route('/history')
@role_required('student')
def student_history():
    """View Past Placement History"""
    student = get_student_from_token()
    if not student:
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    
    # Get selected/placed applications
    history = Application.query.filter_by(
        student_id=student.id,
        status='selected'
    ).order_by(Application.updated_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('student/history.html',
                          history=history.items,
                          pagination=history)


@student_bp.route('/application/<int:app_id>/export-csv')
@role_required('student')
def export_applications(app_id=None):
    """Export applications as CSV (triggers async job)"""
    from backend.tasks import export_student_applications_task
    
    student = get_student_from_token()
    if not student:
        return jsonify({'message': 'Student not found'}), 404
    
    # Trigger async task
    try:
        task = export_student_applications_task.delay(student.user_id)
        
        notification = Notification(
            user_id=request.user_id,
            notification_type='alert',
            subject='Export Started',
            message='Your application export has started. You will receive an email when ready.'
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Export started. You will receive an email shortly.',
            'task_id': task.id
        }), 202
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@student_bp.route('/resume/download')
@role_required('student')
def download_resume():
    """Download student's resume"""
    student = get_student_from_token()
    if not student or not student.resume_path:
        return jsonify({'message': 'Resume not found'}), 404
    
    return send_from_directory(
        os.path.dirname(student.resume_path),
        os.path.basename(student.resume_path)
    )