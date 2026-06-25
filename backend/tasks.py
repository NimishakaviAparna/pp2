"""
Celery Tasks for Background Jobs and Scheduled Tasks
"""
from celery import Celery, shared_task
from celery.schedules import crontab
from datetime import datetime, timedelta
import csv
import io
import os
from functools import wraps

from backend.models import (
    db, User, Student, Company, PlacementDrive, Application,
    ActivityLog, MonthlyReport, Notification, UserRole
)
from backend.email_utils import (
    send_application_deadline_reminder,
    send_interview_reminder,
    send_monthly_report_to_admin,
    send_csv_export_ready
)

celery = Celery(__name__)


def init_celery(app):
    """
    Initialize Celery with Flask app
    """
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    celery.conf.update(app.config)
    return celery


@celery.task(name='send_daily_reminders')
def send_daily_reminders():
    """
    Send daily reminders to students about upcoming deadlines (24 hours before)
    Scheduled to run daily at 9:00 AM
    """
    from flask import current_app
    
    now = datetime.utcnow()
    deadline_start = now + timedelta(hours=23)
    deadline_end = now + timedelta(hours=25)
    
    # Find drives with deadlines in the next 24 hours
    upcoming_drives = PlacementDrive.query.filter(
        PlacementDrive.status == 'approved',
        PlacementDrive.application_deadline.between(deadline_start, deadline_end)
    ).all()
    
    reminders_sent = 0
    
    for drive in upcoming_drives:
        # Get all students who haven't applied yet
        students_applied = Application.query.filter_by(drive_id=drive.id).with_entities(Application.student_id).all()
        applied_ids = [s[0] for s in students_applied]
        
        # Get eligible students
        eligible_students = Student.query.filter(
            Student.id.notin_(applied_ids),
            ~Student.is_blacklisted
        ).all()
        
        for student in eligible_students:
            # Check eligibility
            eligible = True
            
            if drive.min_cgpa and student.cgpa and student.cgpa < drive.min_cgpa:
                eligible = False
            
            if drive.eligible_branches:
                branches = [b.strip() for b in drive.eligible_branches.split(',')]
                if student.branch not in branches:
                    eligible = False
            
            if eligible:
                send_application_deadline_reminder(
                    student.user.email,
                    student.user.name,
                    drive.job_title,
                    drive.company.company_name,
                    drive.application_deadline
                )
                reminders_sent += 1
    
    log = ActivityLog(
        action='DAILY_REMINDERS_SENT',
        description=f'{reminders_sent} deadline reminders sent',
        user_id=1  # System user
    )
    db.session.add(log)
    db.session.commit()
    
    return f'Sent {reminders_sent} deadline reminders'


@celery.task(name='send_interview_reminders')
def send_interview_reminders():
    """
    Send interview reminders 24 hours before scheduled interviews
    Scheduled to run daily at 10:00 AM
    """
    now = datetime.utcnow()
    reminder_start = now + timedelta(hours=23)
    reminder_end = now + timedelta(hours=25)
    
    # Find scheduled interviews in the next 24 hours
    upcoming_interviews = Application.query.filter(
        Application.interview_date.between(reminder_start, reminder_end),
        Application.status.in_(['shortlisted', 'scheduled'])
    ).all()
    
    reminders_sent = 0
    
    for application in upcoming_interviews:
        send_interview_reminder(
            application.student.user.email,
            application.student.user.name,
            application.drive.job_title,
            application.interview_date,
            application.drive.company.company_name
        )
        reminders_sent += 1
    
    log = ActivityLog(
        action='INTERVIEW_REMINDERS_SENT',
        description=f'{reminders_sent} interview reminders sent',
        user_id=1
    )
    db.session.add(log)
    db.session.commit()
    
    return f'Sent {reminders_sent} interview reminders'


@celery.task(name='generate_monthly_report')
def generate_monthly_report():
    """
    Generate monthly placement report and send to admin
    Scheduled to run on the 1st of every month at 12:00 AM
    """
    now = datetime.utcnow()
    month_key = now.strftime('%Y-%m')
    
    # Check if report already generated for this month
    existing_report = MonthlyReport.query.filter_by(month=month_key).first()
    if existing_report and existing_report.sent_to_admin:
        return f'Report already generated for {month_key}'
    
    # Get previous month's data
    prev_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    prev_month_end = now.replace(day=1) - timedelta(days=1)
    
    # Calculate statistics
    total_drives = PlacementDrive.query.filter(
        PlacementDrive.created_at.between(prev_month_start, prev_month_end)
    ).count()
    
    total_applications = Application.query.filter(
        Application.applied_at.between(prev_month_start, prev_month_end)
    ).count()
    
    total_selected = Application.query.filter(
        Application.status == 'selected',
        Application.updated_at.between(prev_month_start, prev_month_end)
    ).count()
    
    # Generate HTML report
    report_html = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .metric {{ margin: 15px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
            </style>
        </head>
        <body>
            <h1>Monthly Placement Report - {prev_month_start.strftime('%B %Y')}</h1>
            
            <div class="metric">
                <h3>Summary Statistics</h3>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Total Drives Conducted</td>
                        <td>{total_drives}</td>
                    </tr>
                    <tr>
                        <td>Total Applications Received</td>
                        <td>{total_applications}</td>
                    </tr>
                    <tr>
                        <td>Total Students Selected</td>
                        <td>{total_selected}</td>
                    </tr>
                    <tr>
                        <td>Placement Success Rate</td>
                        <td>{(total_selected/total_applications*100) if total_applications > 0 else 0:.1f}%</td>
                    </tr>
                </table>
            </div>
            
            <div class="metric">
                <h3>Branch-wise Distribution</h3>
                <table>
                    <tr>
                        <th>Branch</th>
                        <th>Total Students</th>
                        <th>Selected</th>
                        <th>Success Rate</th>
                    </tr>
    """
    
    # Get branch-wise stats
    from sqlalchemy import func
    branch_stats = db.session.query(
        Student.branch,
        func.count(Student.id).label('total'),
        func.count(Application.id).filter(Application.status == 'selected').label('selected')
    ).outerjoin(Application).group_by(Student.branch).all()
    
    for branch, total, selected in branch_stats:
        success_rate = (selected / total * 100) if total > 0 else 0
        report_html += f"""
                    <tr>
                        <td>{branch}</td>
                        <td>{total}</td>
                        <td>{selected or 0}</td>
                        <td>{success_rate:.1f}%</td>
                    </tr>
        """
    
    report_html += """
                </table>
            </div>
            
            <div class="metric">
                <h3>Top Recruiting Companies</h3>
                <table>
                    <tr>
                        <th>Company</th>
                        <th>Students Selected</th>
                    </tr>
    """
    
    # Get top companies
    top_companies = db.session.query(
        Company.company_name,
        func.count(Application.id).label('selected')
    ).join(PlacementDrive).join(Application).filter(
        Application.status == 'selected',
        Application.updated_at.between(prev_month_start, prev_month_end)
    ).group_by(Company.company_name).order_by(func.count(Application.id).desc()).limit(10).all()
    
    for company, selected in top_companies:
        report_html += f"""
                    <tr>
                        <td>{company}</td>
                        <td>{selected}</td>
                    </tr>
        """
    
    report_html += """
                </table>
            </div>
            
            <p style="margin-top: 30px; color: #666;">
                <em>Report generated on {}</em>
            </p>
        </body>
    </html>
    """.format(now.strftime('%Y-%m-%d %H:%M:%S'))
    
    # Save report to database
    report = MonthlyReport(
        month=month_key,
        total_drives=total_drives,
        total_applications=total_applications,
        total_selected=total_selected,
        report_html=report_html,
        sent_to_admin=False
    )
    db.session.add(report)
    db.session.commit()
    
    # Send to admin
    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    if admin:
        send_monthly_report_to_admin(admin.email, report_html)
        report.sent_to_admin = True
        db.session.commit()
    
    log = ActivityLog(
        action='MONTHLY_REPORT_GENERATED',
        description=f'Monthly report generated for {month_key}',
        user_id=1
    )
    db.session.add(log)
    db.session.commit()
    
    return f'Monthly report generated and sent to admin'


@celery.task(name='export_student_applications')
def export_student_applications_task(user_id):
    """
    Export student's applications as CSV
    This is an async task triggered by student
    """
    try:
        user = User.query.get(user_id)
        if not user or user.role != UserRole.STUDENT:
            return 'User not found'
        
        student = user.student_profile
        applications = Application.query.filter_by(student_id=student.id).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'Company Name',
            'Job Title',
            'Location',
            'Application Status',
            'Applied Date',
            'Salary (LPA)',
            'Interview Status'
        ])
        
        # Data rows
        for app in applications:
            writer.writerow([
                app.drive.company.company_name,
                app.drive.job_title,
                app.drive.location,
                app.status.upper(),
                app.applied_at.strftime('%Y-%m-%d %H:%M:%S'),
                f"{app.drive.salary_min}-{app.drive.salary_max}",
                f"Round {app.interview_round}" if app.interview_date else 'Not Scheduled'
            ])
        
        # Save CSV file
        filename = f'applications_{student.id}_{datetime.utcnow().timestamp()}.csv'
        filepath = os.path.join('exports', filename)
        os.makedirs('exports', exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write(output.getvalue())
        
        # Send email with download link
        download_link = f'http://localhost:5000/download/{filename}'
        send_csv_export_ready(user.email, user.name, download_link)
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            notification_type='alert',
            subject='Application Export Ready',
            message=f'Your application export is ready. Check your email for the download link.'
        )
        db.session.add(notification)
        db.session.commit()
        
        return f'Export completed and email sent to {user.email}'
    
    except Exception as e:
        return f'Error: {str(e)}'


@celery.task(name='close_expired_drives')
def close_expired_drives():
    """
    Close placement drives whose application deadline has passed
    Scheduled to run every hour
    """
    now = datetime.utcnow()
    expired_drives = PlacementDrive.query.filter(
        PlacementDrive.status == 'approved',
        PlacementDrive.application_deadline < now
    ).all()
    
    closed_count = 0
    for drive in expired_drives:
        drive.status = 'closed'
        closed_count += 1
    
    if closed_count > 0:
        db.session.commit()
        log = ActivityLog(
            action='DRIVES_CLOSED',
            description=f'{closed_count} expired drives closed',
            user_id=1
        )
        db.session.add(log)
        db.session.commit()
    
    return f'Closed {closed_count} expired drives'


# Celery Beat Schedule Configuration
celery_beat_schedule = {
    'send-daily-reminders': {
        'task': 'send_daily_reminders',
        'schedule': crontab(hour=9, minute=0),  # Every day at 9:00 AM
    },
    'send-interview-reminders': {
        'task': 'send_interview_reminders',
        'schedule': crontab(hour=10, minute=0),  # Every day at 10:00 AM
    },
    'generate-monthly-report': {
        'task': 'generate_monthly_report',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # 1st of month at 12:00 AM
    },
    'close-expired-drives': {
        'task': 'close_expired_drives',
        'schedule': crontab(minute=0),  # Every hour
    },
}