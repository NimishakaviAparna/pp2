"""
Email utilities for sending notifications
"""
from flask_mail import Mail, Message
from flask import render_template_string
from datetime import datetime
import os

mail = Mail()


def send_email(subject, recipients, html_body=None, text_body=None, attachments=None):
    """
    Send email notification
    
    Args:
        subject: Email subject
        recipients: List of recipient emails
        html_body: HTML email body
        text_body: Plain text email body
        attachments: List of file paths to attach
    """
    try:
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            html=html_body,
            body=text_body
        )
        
        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment):
                    msg.attach(
                        filename=os.path.basename(attachment),
                        content_type='application/octet-stream',
                        data=open(attachment, 'rb').read()
                    )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f'Error sending email: {str(e)}')
        return False


def send_welcome_email(user_email, user_name, role):
    """
    Send welcome email to new user
    """
    subject = f'Welcome to Placement Portal - {role.upper()}'
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Welcome to Placement Portal, {user_name}!</h2>
            <p>Your {role} account has been created successfully.</p>
            <p>You can now login at: <a href="http://localhost:5000/auth/login">http://localhost:5000/auth/login</a></p>
            <p>If you have any questions, please contact admin@placement.com</p>
            <br>
            <p>Best regards,<br>Placement Portal Team</p>
        </body>
    </html>
    """
    return send_email(subject, user_email, html_body)


def send_application_deadline_reminder(student_email, student_name, drive_title, company_name, deadline):
    """
    Send application deadline reminder to student
    """
    days_left = (deadline - datetime.utcnow()).days
    subject = f'Reminder: Application Deadline in {days_left} days - {drive_title}'
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Application Deadline Reminder</h2>
            <p>Hi {student_name},</p>
            <p>This is a reminder that the application deadline for <strong>{drive_title}</strong> at <strong>{company_name}</strong> is approaching.</p>
            <p><strong>Deadline:</strong> {deadline.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Days Left:</strong> {days_left}</p>
            <p>Click here to apply: <a href="http://localhost:5000/student/drives">View All Drives</a></p>
            <br>
            <p>Best regards,<br>Placement Portal Team</p>
        </body>
    </html>
    """
    return send_email(subject, student_email, html_body)


def send_interview_reminder(student_email, student_name, drive_title, interview_date, company_name):
    """
    Send interview reminder to student
    """
    subject = f'Interview Reminder - {drive_title} at {company_name}'
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Interview Scheduled</h2>
            <p>Hi {student_name},</p>
            <p>Your interview for <strong>{drive_title}</strong> at <strong>{company_name}</strong> has been scheduled.</p>
            <p><strong>Date & Time:</strong> {interview_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Please make sure to be available at the scheduled time.</p>
            <p>If you have any questions or need to reschedule, please contact the company directly.</p>
            <br>
            <p>Best regards,<br>Placement Portal Team</p>
        </body>
    </html>
    """
    return send_email(subject, student_email, html_body)


def send_application_status_update(student_email, student_name, drive_title, company_name, status):
    """
    Send application status update to student
    """
    status_messages = {
        'shortlisted': 'Congratulations! You have been shortlisted.',
        'selected': 'Congratulations! You have been selected.',
        'rejected': 'Thank you for applying. Unfortunately, you were not selected at this time.',
        'applied': 'Your application has been received.'
    }
    
    message = status_messages.get(status, 'Your application status has been updated.')
    subject = f'Application Status Update - {drive_title}'
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Application Status Update</h2>
            <p>Hi {student_name},</p>
            <p><strong>{message}</strong></p>
            <p><strong>Position:</strong> {drive_title}</p>
            <p><strong>Company:</strong> {company_name}</p>
            <p><strong>Status:</strong> {status.upper()}</p>
            <p>Login to your account to view more details: <a href="http://localhost:5000/student/applications">View Applications</a></p>
            <br>
            <p>Best regards,<br>Placement Portal Team</p>
        </body>
    </html>
    """
    return send_email(subject, student_email, html_body)


def send_monthly_report_to_admin(admin_email, report_html):
    """
    Send monthly placement report to admin
    """
    subject = f'Monthly Placement Report - {datetime.utcnow().strftime("%B %Y")}'
    return send_email(subject, admin_email, html_body=report_html)


def send_company_approval_notification(company_email, company_name, approved=True):
    """
    Send company approval/rejection notification
    """
    if approved:
        subject = 'Your Company Has Been Approved!'
        status_msg = 'approved'
        action_msg = 'You can now create placement drives on the portal.'
    else:
        subject = 'Company Registration - Further Review Required'
        status_msg = 'rejected'
        action_msg = 'Please contact admin@placement.com for more information.'
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Company Registration Update</h2>
            <p>Hi {company_name},</p>
            <p>Your company registration has been <strong>{status_msg}</strong>.</p>
            <p>{action_msg}</p>
            <p>Login to your account: <a href="http://localhost:5000/auth/login">http://localhost:5000/auth/login</a></p>
            <br>
            <p>Best regards,<br>Placement Portal Team</p>
        </body>
    </html>
    """
    return send_email(subject, company_email, html_body)


def send_csv_export_ready(student_email, student_name, download_link):
    """
    Send notification when CSV export is ready
    """
    subject = 'Your Application Export is Ready'
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Export Ready</h2>
            <p>Hi {student_name},</p>
            <p>Your application export is ready for download.</p>
            <p><a href="{download_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download CSV</a></p>
            <p>The download link will expire in 24 hours.</p>
            <br>
            <p>Best regards,<br>Placement Portal Team</p>
        </body>
    </html>
    """
    return send_email(subject, student_email, html_body)