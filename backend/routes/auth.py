"""
Authentication Routes
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, flash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from functools import wraps
import jwt
from datetime import datetime

from backend.models import db, User, UserRole, Student, Company, ActivityLog
from config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def token_required(f):
    """Decorator to check JWT token from cookies or headers"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('jwt_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            if request.is_json:
                return jsonify({'message': 'Token missing!'}), 401
            flash('Please login to continue', 'error')
            return redirect(url_for('auth.login'))
        
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload.get('user_id')
            request.user_role = payload.get('role')
            request.user_email = payload.get('email')
        except jwt.ExpiredSignatureError:
            if request.is_json:
                return jsonify({'message': 'Token expired'}), 401
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth.login'))
        except:
            if request.is_json:
                return jsonify({'message': 'Invalid token'}), 401
            flash('Invalid session. Please login again.', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated


def role_required(required_role):
    """Decorator to check user role"""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.user_role != required_role:
                if request.is_json:
                    return jsonify({'message': f'Access denied. {required_role} only'}), 403
                flash(f'Access denied. This page is for {required_role}s only.', 'error')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated
    return decorator


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register new Student or Company"""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    data = request.get_json() if request.is_json else request.form
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    role = data.get('role', 'student')
    
    # Validation
    if not all([name, email, password, role]):
        msg = 'Missing required fields'
        if request.is_json:
            return jsonify({'message': msg}), 400
        flash(msg, 'error')
        return render_template('auth/register.html', selected_role=role, form_name=name, form_email=email)
    
    if password != confirm_password:
        msg = 'Passwords do not match'
        if request.is_json:
            return jsonify({'message': msg}), 400
        flash(msg, 'error')
        return render_template('auth/register.html', selected_role=role, form_name=name, form_email=email)
    
    if role not in ['student', 'company']:
        msg = 'Invalid role'
        if request.is_json:
            return jsonify({'message': msg}), 400
        flash(msg, 'error')
        return render_template('auth/register.html')
    
    if len(password) < 6:
        msg = 'Password must be at least 6 characters'
        if request.is_json:
            return jsonify({'message': msg}), 400
        flash(msg, 'error')
        return render_template('auth/register.html', selected_role=role, form_name=name, form_email=email)
    
    # Check if email exists
    if User.query.filter_by(email=email).first():
        msg = 'Email already registered'
        if request.is_json:
            return jsonify({'message': msg}), 409
        flash(msg, 'error')
        return render_template('auth/register.html', selected_role=role, form_name=name, form_email=email)
    
    try:
        # Create User
        user = User(
            name=name,
            email=email,
            role=UserRole(role),
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        # Create Profile
        if role == 'student':
            student = Student(user_id=user.id, branch='', year='')
            db.session.add(student)
        elif role == 'company':
            company = Company(
                user_id=user.id,
                company_name=name,
                industry='',
                location='',
                approval_status='pending'
            )
            db.session.add(company)
        
        # Log activity
        log = ActivityLog(
            action=f'{role.upper()}_REGISTERED',
            description=f'New {role} registered: {email}',
            user_id=user.id
        )
        db.session.add(log)
        db.session.commit()
        
        msg = 'Registration successful. Please login.'
        if request.is_json:
            return jsonify({'message': msg, 'redirect': url_for('auth.login')}), 201
        flash(msg, 'success')
        return redirect(url_for('auth.login'))
    
    except Exception as e:
        db.session.rollback()
        msg = f'Error: {str(e)}'
        if request.is_json:
            return jsonify({'message': msg}), 500
        flash(msg, 'error')
        return render_template('auth/register.html', selected_role=role)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login User"""
    if request.method == 'GET':
        return render_template('auth/login.html', selected_role='student')
    
    data = request.get_json() if request.is_json else request.form
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'student')
    
    if not all([email, password, role]):
        msg = 'Missing credentials'
        if request.is_json:
            return jsonify({'message': msg}), 400
        flash(msg, 'error')
        return render_template('auth/login.html', selected_role=role, form_email=email)
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        msg = 'Invalid email or password'
        if request.is_json:
            return jsonify({'message': msg}), 401
        flash(msg, 'error')
        return render_template('auth/login.html', selected_role=role, form_email=email)
    
    if user.role.value != role:
        msg = 'Invalid role for this user'
        if request.is_json:
            return jsonify({'message': msg}), 401
        flash(msg, 'error')
        return render_template('auth/login.html', selected_role=role, form_email=email)
    
    if not user.is_active:
        msg = 'User account is inactive or blacklisted'
        if request.is_json:
            return jsonify({'message': msg}), 403
        flash(msg, 'error')
        return render_template('auth/login.html', selected_role=role, form_email=email)
    
    # Generate JWT Token
    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value
        }
    )
    
    # Log activity
    log = ActivityLog(
        action='LOGIN',
        description=f'{user.role.value} logged in: {email}',
        user_id=user.id
    )
    db.session.add(log)
    db.session.commit()
    
    response_data = {
        'token': token,
        'name': user.name,
        'email': user.email,
        'role': user.role.value,
        'user_id': user.id
    }
    
    # For API requests
    if request.is_json:
        return jsonify(response_data), 200
    
    # For form requests - set cookie and redirect
    resp = make_response(redirect(url_for(f'{role}_dashboard')))
    resp.set_cookie('jwt_token', token, httponly=True, max_age=2592000)
    resp.set_cookie('user_id', str(user.id), httponly=True, max_age=2592000)
    resp.set_cookie('user_role', role, httponly=True, max_age=2592000)
    resp.set_cookie('user_name', user.name, httponly=True, max_age=2592000)
    resp.set_cookie('user_email', user.email, httponly=True, max_age=2592000)
    return resp


@auth_bp.route('/logout')
def logout():
    """Logout User"""
    resp = make_response(redirect(url_for('auth.login')))
    resp.delete_cookie('jwt_token')
    resp.delete_cookie('user_id')
    resp.delete_cookie('user_role')
    resp.delete_cookie('user_name')
    resp.delete_cookie('user_email')
    flash('Logged out successfully', 'success')
    return resp


@auth_bp.route('/me')
@token_required
def get_current_user():
    """Get Current User Info"""
    user = User.query.get(request.user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(user.to_dict()), 200


@auth_bp.route('/verify-token')
@token_required
def verify_token():
    """Verify if token is valid"""
    return jsonify({
        'valid': True,
        'user_id': request.user_id,
        'role': request.user_role
    }), 200