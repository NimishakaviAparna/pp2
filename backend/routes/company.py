"""
Company Routes
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from datetime import datetime
from functools import wraps

from backend.models import (
    db, User, Company, PlacementDrive, Application, UserRole,
    ActivityLog, Notification
)
from .auth import token_required, role_required

company_bp = Blueprint('company', __name__, url_prefix='/company')


def get_company_from_token():
    """Get company object from JWT token"""
    user = User.query.get(request.user_id)
    if not user or user.role != UserRole.COMPANY:
        return None
    return user.company_profile


@company_bp.route('/dashboard')
@role_required('company')
def company_dashboard():
    """Company Dashboard"""
    company = get_company_from_token()
    if not company:
        flash('Company profile not found', 'error')
        return redirect(url_for('auth.login'))
    
    # Get Stats
    total_drives = len(company.placement_drives)
    active_drives = len([d for d in company.placement_drives if d.status == 'approved'])
    total_applications = sum(len(d.applications) for d in company.placement_drives)
    selected = sum(len([a for a in d.applications if a.status == 'selected']) for d in company.placement_drives)
    
    return render_template('company/dashboard.html',
                          company=company,
                          stats={
                              'total_drives': total_drives,
                              'active_drives': active_drives,
                              'total_applications': total_applications,
                              'total_selected': selected
                          },
                          drives=company.placement_drives[:5])


@company_bp.route('/profile')
@role_required('company')
def company_profile():
    """View Company Profile"""
    company = get_company_from_token()
    if not company:
        return redirect(url_for('auth.login'))
    
    return render_template('company/profile.html', company=company)


@company_bp.route('/profile/edit', methods=['GET', 'POST'])
@role_required('company')
def edit_profile():
    """Edit Company Profile"""
    company = get_company_from_token()
    if not company:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        company.company_name = request.form.get('company_name', company.company_name)
        company.industry = request.form.get('industry', company.industry)
        company.location = request.form.get('location', company.location)
        company.website = request.form.get('website', company.website)
        company.phone = request.form.get('phone', company.phone)
        company.description = request.form.get('description', company.description)
        
        db.session.commit()
        
        log = ActivityLog(
            action='COMPANY_PROFILE_UPDATED',
            description=f'Company {company.company_name} updated profile',
            user_id=request.user_id
        )
        db.session.add(log)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': 'Profile updated'}), 200
        flash('Profile updated successfully', 'success')
        return redirect(url_for('company.company_profile'))
    
    return render_template('company/edit_profile.html', company=company)


@company_bp.route('/drives')
@role_required('company')
def company_drives():
    """View Company's Placement Drives"""
    company = get_company_from_token()
    if not company:
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all', type=str)
    
    query = PlacementDrive.query.filter_by(company_id=company.id)
    
    if status != 'all':
        query = query.filter(PlacementDrive.status == status)
    
    drives = query.order_by(PlacementDrive.application_deadline.desc()).paginate(page=page, per_page=10)
    
    return render_template('company/drives.html',
                          drives=drives.items,
                          pagination=drives,
                          status=status)


@company_bp.route('/drive/create', methods=['GET', 'POST'])
@role_required('company')
def create_drive():
    """Create Placement Drive"""
    company = get_company_from_token()
    if not company:
        return redirect(url_for('auth.login'))
    
    if company.approval_status != 'approved':
        flash('Your company is not approved yet. Please wait for admin approval.', 'error')
        return redirect(url_for('company.company_dashboard'))
    
    if request.method == 'POST':
        try:
            deadline = datetime.fromisoformat(request.form.get('application_deadline'))
            
            drive = PlacementDrive(
                company_id=company.id,
                job_title=request.form.get('job_title'),
                job_description=request.form.get('job_description'),
                location=request.form.get('location'),
                job_type=request.form.get('job_type'),
                min_cgpa=float(request.form.get('min_cgpa')) if request.form.get('min_cgpa') else None,
                eligible_branches=request.form.get('eligible_branches'),
                eligible_years=request.form.get('eligible_years'),
                salary_min=float(request.form.get('salary_min')),
                salary_max=float(request.form.get('salary_max')),
                application_deadline=deadline,
                status='pending'  # Requires admin approval
            )
            
            db.session.add(drive)
            
            log = ActivityLog(
                action='DRIVE_CREATED',
                description=f'Drive {drive.job_title} created by {company.company_name}',
                user_id=request.user_id
            )
            db.session.add(log)
            db.session.commit()
            
            # Notify admin
            admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
            if admin_user:
                notification = Notification(
                    user_id=admin_user.id,
                    notification_type='alert',
                    subject='New Placement Drive for Review',
                    message=f'{company.company_name} created a new drive: {drive.job_title}'
                )
                db.session.add(notification)
                db.session.commit()
            
            if request.is_json:
                return jsonify({'message': 'Drive created. Waiting for admin approval.'}), 201
            flash('Drive created successfully. Waiting for admin approval.', 'success')
            return redirect(url_for('company.company_drives'))
        
        except Exception as e:
            db.session.rollback()
            msg = f'Error: {str(e)}'
            if request.is_json:
                return jsonify({'message': msg}), 500
            flash(msg, 'error')
    
    return render_template('company/create_drive.html', company=company)


@company_bp.route('/drive/<int:drive_id>/edit', methods=['GET', 'POST'])
@role_required('company')
def edit_drive(drive_id):
    """Edit Placement Drive"""
    drive = PlacementDrive.query.get_or_404(drive_id)
    company = get_company_from_token()
    
    if drive.company_id != company.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('company.company_drives'))
    
    if request.method == 'POST':
        try:
            drive.job_title = request.form.get('job_title', drive.job_title)
            drive.job_description = request.form.get('job_description', drive.job_description)
            drive.location = request.form.get('location', drive.location)
            drive.job_type = request.form.get('job_type', drive.job_type)
            drive.min_cgpa = float(request.form.get('min_cgpa')) if request.form.get('min_cgpa') else None
            drive.eligible_branches = request.form.get('eligible_branches', drive.eligible_branches)
            drive.eligible_years = request.form.get('eligible_years', drive.eligible_years)
            drive.salary_min = float(request.form.get('salary_min', drive.salary_min))
            drive.salary_max = float(request.form.get('salary_max', drive.salary_max))
            
            db.session.commit()
            
            log = ActivityLog(
                action='DRIVE_UPDATED',
                description=f'Drive {drive.job_title} updated',
                user_id=request.user_id
            )
            db.session.add(log)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'message': 'Drive updated'}), 200
            flash('Drive updated successfully', 'success')
            return redirect(url_for('company.company_drives'))
        
        except Exception as e:
            db.session.rollback()
            msg = f'Error: {str(e)}'
            if request.is_json:
                return jsonify({'message': msg}), 500
            flash(msg, 'error')
    
    return render_template('company/edit_drive.html', drive=drive)


@company_bp.route('/drive/<int:drive_id>/applications')
@role_required('company')
def view_applications(drive_id):
    """View Applicants for a Drive"""
    drive = PlacementDrive.query.get_or_404(drive_id)
    company = get_company_from_token()
    
    if drive.company_id != company.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('company.company_drives'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all', type=str)
    
    query = Application.query.filter_by(drive_id=drive_id)
    
    if status != 'all':
        query = query.filter(Application.status == status)
    
    applications = query.order_by(Application.applied_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('company/applications.html',
                          drive=drive,
                          applications=applications.items,
                          pagination=applications,
                          status=status)


@company_bp.route('/application/<int:app_id>/status', methods=['POST'])
@role_required('company')
def update_application_status(app_id):
    """Update Application Status"""
    application = Application.query.get_or_404(app_id)
    company = get_company_from_token()
    
    if application.drive.company_id != company.id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json() or request.form
    new_status = data.get('status')
    
    if new_status not in ['applied', 'shortlisted', 'selected', 'rejected', 'withdrawn']:
        return jsonify({'message': 'Invalid status'}), 400
    
    old_status = application.status
    application.status = new_status
    application.updated_at = datetime.utcnow()
    
    if new_status == 'selected':
        application.interview_date = None  # Clear interview date when selected
    
    db.session.commit()
    
    # Notify student
    notification = Notification(
        user_id=application.student.user_id,
        notification_type='alert',
        subject=f'Application Status Updated',
        message=f'Your application for {application.drive.job_title} at {application.drive.company.company_name} is now {new_status}.'
    )
    db.session.add(notification)
    db.session.commit()
    
    log = ActivityLog(
        action='APPLICATION_STATUS_UPDATED',
        description=f'Application status changed from {old_status} to {new_status}',
        user_id=request.user_id
    )
    db.session.add(log)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'message': 'Status updated'}), 200
    flash('Application status updated', 'success')
    return redirect(url_for('company.view_applications', drive_id=application.drive_id))


@company_bp.route('/application/<int:app_id>/schedule-interview', methods=['POST'])
@role_required('company')
def schedule_interview(app_id):
    """Schedule Interview"""
    application = Application.query.get_or_404(app_id)
    company = get_company_from_token()
    
    if application.drive.company_id != company.id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json() or request.form
    
    try:
        interview_date = datetime.fromisoformat(data.get('interview_date'))
        interview_round = int(data.get('interview_round', 1))
        
        application.interview_date = interview_date
        application.interview_round = interview_round
        application.status = 'shortlisted'  # Shortlist when interview scheduled
        
        db.session.commit()
        
        # Notify student
        notification = Notification(
            user_id=application.student.user_id,
            notification_type='alert',
            subject='Interview Scheduled',
            message=f'Your interview for {application.drive.job_title} (Round {interview_round}) is scheduled on {interview_date.strftime("%Y-%m-%d %H:%M")}'
        )
        db.session.add(notification)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': 'Interview scheduled'}), 200
        flash('Interview scheduled successfully', 'success')
        return redirect(url_for('company.view_applications', drive_id=application.drive_id))
    
    except Exception as e:
        return jsonify({'message': str(e)}), 400