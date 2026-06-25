from flask import Flask, render_template, request, redirect, url_for, flash, make_response, Blueprint
import requests
from dotenv import load_dotenv
import os
import jwt                          
from functools import wraps
from jinja2 import ChoiceLoader, FileSystemLoader

load_dotenv()  

app = Flask(__name__, template_folder="templates", static_folder="static")
app.jinja_loader = ChoiceLoader([
    FileSystemLoader('templates'),
    FileSystemLoader('templates/landing_page/templates'),
])
app.jinja_env.globals.update(range=range, enumerate=enumerate, zip=zip)
app.secret_key = os.environ.get('SECRET_KEY')
JWT_SECRET = os.environ.get('SECRET_KEY')

landing_static = Blueprint(
    'landing_static',
    __name__,
    static_folder='templates/landing_page/static',
    static_url_path='/landing_static'
)

app.register_blueprint(landing_static)

def decode_token(token):
    """
    Decodes the JWT token and returns the payload.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None  
    except jwt.InvalidTokenError:
        return None   

def login_required(required_role=None):
    """
    Decorator factory that protects routes.
    
    Usage:
    @login_required()                    → just checks if logged in
    @login_required(required_role='admin')    → checks if role is admin
    @login_required(required_role='student')  → checks if role is student
    @login_required(required_role='company')  → checks if role is company
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            token = request.cookies.get('jwt_token')

            if not token:
                flash('Please login to continue', 'error')
                return redirect(url_for('login'))

            payload = decode_token(token)

            if not payload:
                flash('Session expired. Please login again.', 'error')
                return redirect(url_for('login'))

            if required_role:
                user_role = payload.get('role')
                if user_role != required_role:
                    flash(f'Access denied. This page is for {required_role}s only.', 'error')
                    return redirect(url_for('login'))

            return f(*args, **kwargs)

        return decorated_function
    return decorator

STATS = [
    {"icon": "bi-people-fill",      "number": "5,000+", "label": "Students"},
    {"icon": "bi-building-fill",     "number": "250+",   "label": "Partner Companies"},
    {"icon": "bi-graph-up-arrow",   "number": "4,500+", "label": "Successful Placements"},
    {"icon": "bi-mortarboard-fill", "number": "12",     "label": "Avg Package (LPA)"},
]

JOBS = [
    {"title": "Accountant",       "company": "EY",        "location": "Anywhere in India", "last_date": "2025-11-19"},
    {"title": "Data Analyst",     "company": "Infosys",   "location": "Pune",              "last_date": "2025-12-05"},
    {"title": "Business Analyst", "company": "Accenture", "location": "Mumbai",            "last_date": "2025-11-28"},
]

PLACEMENT_STATS = {
    "courses": ["CS", "IT", "ENTC", "Mechanical", "Civil"],
    "rows": [
        {"label": "Highest CTC", "icon": "bi-currency-rupee", "icon_color": "#0e6b7a",
         "data": ["₹ 48 LPA", "₹ 36 LPA", "₹ 30 LPA", "₹ 30 LPA", "₹ 24 LPA"]},
        {"label": "Avg. CTC",    "icon": "bi-star-fill",      "icon_color": "#f5c518",
         "data": ["₹ 18 LPA", "₹ 14.4 LPA", "₹ 12 LPA", "₹ 12 LPA", "₹ 12 LPA"]},
        {"label": "Lowest CTC",  "icon": "bi-check-circle-fill", "icon_color": "#0e6b7a",
         "data": ["₹ 7.2 LPA", "₹ 5.4 LPA", "₹ 4.2 LPA", "₹ 4.2 LPA", "₹ 4.8 LPA"]},
    ]
}

COMPANIES = [
    {"name": "ICICI Bank",          "css_class": "logo-icici",    "display": "ICICI BANK"},
    {"name": "Hero",                "css_class": "logo-hero",     "display": "▪ Hero"},
    {"name": "HP",                  "css_class": "logo-hp",       "display": "hp"},
    {"name": "Accenture",           "css_class": "logo-accenture","display": "accenture>"},
    {"name": "Aditya Birla Group",  "css_class": "logo-aditya",   "display": "Aditya Birla"},
    {"name": "Airtel",              "css_class": "logo-airtel",   "display": "airtel"},
    {"name": "Amazon",              "css_class": "logo-amazon",   "display": "amazon"},
    {"name": "American Express",    "css_class": "logo-amex",     "display": "Amex"},
    {"name": "Axis Bank",           "css_class": "logo-axis",     "display": "AXIS BANK"},
    {"name": "Infosys",             "css_class": "logo-infosys",  "display": "Infosys"},
    {"name": "J.P. Morgan",         "css_class": "logo-jpmorgan", "display": "J.P.Morgan", "highlight": True},
    {"name": "KPMG",                "css_class": "logo-kpmg",     "display": "KPMG"},
    {"name": "Larsen & Toubro",     "css_class": "logo-lt",       "display": "L&T"},
    {"name": "Jindal Steel",        "css_class": "logo-jindal",   "display": "JINDAL Steel"},
]

TESTIMONIALS = [
    {"name": "Adtiya Bhattacharya",      "role": "Accountant @ Finprov Learning",
     "text": "Lakshya's holistic approach to accounting education, guided by industry-experienced faculty, helped me gain real-world insights beyond textbooks. The institute's mock exams were invaluable in preparing for ACCA, strengthening both my subject knowledge and exam strategies."},
    {"name": "Pallav",    "role": "SWD @ Microsoft",
     "text": "My US CMA journey with Lakshya was truly transformative. The structured study plan, expert guidance, and exam-focused approach helped me become India's top scorer (Jan 2024). Thanks to this strong foundation, I now work as an FP&A Analyst."},
    {"name": "Sundar Pichai", "role": "CEO @ Google",
     "text": "Lakshya provided me the knowledge, skills, and confidence to excel in accounting and finance. Building on this foundation, I founded Grandworth Financial Consultancy and now work at EY."},
]

FAQS = [
    {"q": "Who can participate in the VIT Placement Drive?",
     "a": "All enrolled students who have completed their course modules and have an active portal account are eligible."},
    {"q": "How do I register for the placement drive?",
     "a": "Create an account, complete your profile with resume and academic details, and you are automatically eligible to apply."},
    {"q": "Is there a registration fee for students?",
     "a": "No, registration is completely free for all enrolled IIC Lakshya students."},
    {"q": "When and where will the placement drive take place?",
     "a": "Drives are conducted throughout the year at various IIC Lakshya centers. Check the Announcements section for dates."},
]

YOUTUBE_EMBED = "https://www.youtube.com/embed/cZ590Z8ROws"


@app.route('/')
def index():
    return render_template(
        'index.html',
        stats=STATS,
        jobs=JOBS,
        placement_stats=PLACEMENT_STATS,
        companies=COMPANIES,
        testimonials=TESTIMONIALS,
        faqs=FAQS,
        youtube_embed=YOUTUBE_EMBED,
    )  

# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
@login_required(required_role='admin') 
def admin_dashboard():
    return render_template("admin/dashboard.html", 
                       role="admin",
                       total_students=150,
                       total_companies=25,
                       total_drives=45,
                       total_applications=380,
                       total_shortlisted=85,
                       total_selected=62,
                       pending_companies=[],
                       pending_drives=[])

@app.route("/admin/students")
@login_required(required_role='admin') 
def admin_students():
    return render_template("admin/students.html",
                           role="admin",
                           students=[])

@app.route("/admin/student/<int:id>")
@login_required(required_role='admin') 
def student_detail(id):
    return render_template("admin/student_detail.html",
                           role="admin",
                           student={
                               "id": id,
                               "name": "Test Student",
                               "email": "test@email.com",
                               "branch": "Computer Engineering",
                               "year": "Final Year",
                               "cgpa": 8.5,
                               "status": "active",
                               "resume_url": None
                           },
                           placement_stats={
                               "total_applications": 5,
                               "shortlisted": 2,
                               "selected": 1
                           },
                           applications=[])

@app.route("/admin/students/<int:id>")
@login_required(required_role='admin') 
def admin_student_detail_plural(id):
    return render_template("admin/student_detail.html",
                           role="admin",
                           student={
                               "id": id,
                               "name": "Test Student",
                               "email": "test@email.com",
                               "branch": "Computer Engineering",
                               "year": "Final Year",
                               "cgpa": 8.5,
                               "status": "active",
                               "resume_url": None
                           },
                           placement_stats={
                               "total_applications": 5,
                               "shortlisted": 2,
                               "selected": 1
                           },
                           applications=[])

@app.route("/admin/companies")
@login_required(required_role='admin') 
def admin_companies():
    return render_template("admin/companies.html",
                           role="admin",
                           companies=[])

@app.route("/admin/drives")
@login_required(required_role='admin') 
def admin_drives():
    return render_template("admin/drives.html",
                           role="admin",
                           drives=[],
                           company_list=[])

@app.route("/admin/drives/<int:id>")
@login_required(required_role='admin') 
def admin_drive_detail(id):
    return render_template("admin/drive_detail.html",
                           role="admin",
                           drive={
                               "id": id,
                               "role": "Software Engineer",
                               "company": "Tech Corp",
                               "location": "Bangalore",
                               "type": "Full Time",
                               "ctc": "8 LPA",
                               "description": "We are looking for talented software engineers to join our team.",
                               "status": "active"
                           },
                           applications=[])

@app.route("/admin/applications")
@login_required(required_role='admin') 
def admin_applications():
    return render_template("admin/applications.html",
                           role="admin",
                           applications=[],
                           company_list=[],
                           drive_list=[])

@app.route("/admin/reports")
@login_required(required_role='admin') 
def admin_reports():
    return render_template("admin/reports.html",
                           role="admin",
                           report={
                               "total_students": 100,
                               "total_applications": 300,
                               "total_selected": 60,
                               "placement_percentage": 60
                           },
                           branch_report=[],
                           company_report=[])

@app.route("/admin/historical")
@login_required(required_role='admin') 
def admin_historical():
    return render_template("admin/historical.html",
                           role="admin",
                           available_years=["2023-24","2022-23"],
                           historical={
                               "total_students": 120,
                               "total_companies": 25,
                               "total_selected": 75,
                               "placement_percentage": 62,
                               "branch_data": [],
                               "drives": []
                           })


# ---------------- STUDENT DASHBOARD ----------------

@app.route("/student/dashboard")
@login_required(required_role='student')
def student_dashboard():
    return render_template(
        "student/dashboard.html",
        role="student",
        stats={
            "total_applications": 5,
            "shortlisted": 2,
            "selected": 1,
            "upcoming": 3
        },
        companies=[
            {
                "id": 1,
                "name": "Tech Corporation",
                "industry": "Technology",
                "location": "Bangalore",
                "drives_count": 3
            },
            {
                "id": 2,
                "name": "Global Systems",
                "industry": "IT Services",
                "location": "Mumbai",
                "drives_count": 2
            },
            {
                "id": 3,
                "name": "Innovate Solutions",
                "industry": "Software",
                "location": "Pune",
                "drives_count": 4
            }
        ],
        drives=[
            {
                "id": 1,
                "company_name": "Tech Corporation",
                "role": "Software Engineer",
                "type": "Full Time",
                "ctc": "8 LPA",
                "location": "Bangalore",
                "deadline": "2026-02-28"
            },
            {
                "id": 2,
                "company_name": "Global Systems",
                "role": "Frontend Developer",
                "type": "Full Time",
                "ctc": "6 LPA",
                "location": "Mumbai",
                "deadline": "2026-03-15"
            },
            {
                "id": 3,
                "company_name": "Innovate Solutions",
                "role": "Backend Developer",
                "type": "Full Time",
                "ctc": "7 LPA",
                "location": "Pune",
                "deadline": "2026-03-01"
            }
        ]
    )


@app.route("/student/profile")
@login_required(required_role='student')
def student_profile():
    return render_template(
        "student/profile.html",
        role="student",
        student={
            "name": "Test Student",
            "email": "test@email.com",
            "branch": "Computer Engineering",
            "year": "Final Year",
            "cgpa": 8.5,
            "resume_url": None
        }
    )


@app.route("/student/edit-profile")
@login_required(required_role='student')
def student_edit_profile():
    return render_template(
        "student/edit_profile.html",
        role="student",
        student={
            "name": "Test Student",
            "email": "test@email.com",
            "branch": "Computer Engineering",
            "year": "Final Year",
            "cgpa": 8.5,
            "resume_url": None
        }
    )


@app.route("/student/company/<int:id>")
@login_required(required_role='student')
def student_company_detail(id):
    company = {
        "id": id,
        "name": "Tech Corporation",
        "industry": "Technology Services",
        "location": "Bangalore, India",
        "website": "www.techcorp.com",
        "employees": "1000-5000",
        "description": "Tech Corporation is a leading technology company specializing in software development, cloud solutions, and digital transformation. We work with Fortune 500 companies to deliver innovative solutions that drive business growth and digital excellence.",
        "drives_count": 5,
        "hired_count": 25,
        "rating": 4.5
    }
    
    company_drives = [
        {
            "id": 1,
            "role": "Software Engineer",
            "type": "Full Time",
            "ctc": "8 LPA",
            "location": "Bangalore",
            "deadline": "2026-02-28",
            "department": "Engineering"
        },
        {
            "id": 2,
            "role": "Frontend Developer",
            "type": "Full Time",
            "ctc": "6 LPA",
            "location": "Bangalore",
            "deadline": "2026-03-15",
            "department": "Engineering"
        },
        {
            "id": 3,
            "role": "Backend Developer",
            "type": "Full Time",
            "ctc": "7 LPA",
            "location": "Bangalore",
            "deadline": "2026-03-01",
            "department": "Engineering"
        }
    ]
    
    return render_template(
        "student/company_detail.html",
        role="student",
        company=company,
        company_drives=company_drives
    )


@app.route("/student/drive/<int:id>")
@login_required(required_role='student')
def student_drive_detail(id):
    drive = {
        "id": id,
        "company_id": 1,
        "company_name": "Tech Corporation",
        "role": "Software Engineer",
        "type": "Full Time",
        "ctc": "8 LPA",
        "location": "Bangalore",
        "deadline": "2026-02-28",
        "department": "Computer Science",
        "experience": "Entry Level",
        "description": "We are looking for a talented Software Engineer to join our dynamic team. You will be responsible for developing high-quality software solutions, working with cutting-edge technologies, and contributing to innovative projects that impact millions of users worldwide.",
        "min_cgpa": "6.5",
        "branches": "CS, IT, ECE"
    }
    
    has_applied = id == 1  
    
    return render_template(
        "student/drive_detail.html",
        role="student",
        drive=drive,
        has_applied=has_applied
    )


@app.route("/student/apply/<int:drive_id>", methods=["POST"])
@login_required(required_role='student')
def apply_drive(drive_id):
    return redirect(url_for("student_applied"))


@app.route("/student/drives")
@login_required(required_role='student')
def student_drives():
    return render_template(
        "student/drives.html",
        role="student",
        drives=[
            {
                "id": 1,
                "company": "TCS",
                "role": "Software Engineer",
                "ctc": 7,
                "deadline": "2026-03-15"
            }
        ]
    )


@app.route("/student/applied")
@login_required(required_role='student')
def student_applied():
    return render_template(
        "student/applied.html",
        role="student",
        applications=[
            {
                "id": 1,
                "company": "Infosys",
                "role": "Backend Developer",
                "ctc": 8,
                "status": "Applied",
                "date": "2026-03-01"
            }
        ]
    )


@app.route("/student/history")
@login_required(required_role='student')
def student_history():
    return render_template(
        "student/history.html",
        role="student",
        history=[
            {
                "company": "TCS",
                "role": "Software Engineer",
                "ctc": 7,
                "status": "Selected",
                "date": "2025-11-20"
            }
        ]
    )

# ---------------- COMPANY DASHBOARD ----------------

@app.route("/company/dashboard")
@login_required(required_role='company')
def company_dashboard():
    return render_template(
        "company/dashboard.html",
        role="company",
        company={
            "name": "Test Company",
            "description": "Leading technology company specializing in software development and digital transformation solutions.",
            "location": "Mumbai, India",
            "work_mode": "Hybrid",
            "logo": None
        },
        stats={
            "total_drives": 3,
            "active_drives": 2,
            "total_applications": 150,
            "shortlisted": 40,
            "students_placed": 10
        },
        ongoing_drives=[
            {
                "id": 1,
                "name": "Backend Developer",
                "icon": None,
                "applicant_avatars": [
                    "/static/avatar1.jpg",
                    "/static/avatar2.jpg", 
                    "/static/avatar3.jpg",
                    "/static/avatar4.jpg"
                ],
                "completion_pct": 75
            },
            {
                "id": 2,
                "name": "Frontend Developer",
                "icon": None,
                "applicant_avatars": [
                    "/static/avatar5.jpg",
                    "/static/avatar6.jpg",
                    "/static/avatar7.jpg"
                ],
                "completion_pct": 60
            }
        ]
    )


@app.route("/dashboard")
@login_required(required_role='company')
def dashboard():
    return render_template(
        "company/dashboard.html",
        role="company",
        company={
            "name": "Test Company",
            "description": "Leading technology company specializing in software development and digital transformation solutions.",
            "location": "Mumbai, India",
            "work_mode": "Hybrid",
            "logo": None
        },
        stats={
            "total_drives": 3,
            "active_drives": 2,
            "total_applications": 150,
            "shortlisted": 40,
            "students_placed": 10
        },
        ongoing_drives=[
            {
                "id": 1,
                "name": "Backend Developer",
                "icon": None,
                "applicant_avatars": [
                    "/static/avatar1.jpg",
                    "/static/avatar2.jpg", 
                    "/static/avatar3.jpg",
                    "/static/avatar4.jpg"
                ],
                "completion_pct": 75
            },
            {
                "id": 2,
                "name": "Frontend Developer",
                "icon": None,
                "applicant_avatars": [
                    "/static/avatar5.jpg",
                    "/static/avatar6.jpg",
                    "/static/avatar7.jpg"
                ],
                "completion_pct": 60
            }
        ]
    )


@app.route("/company/drives")
@login_required(required_role='company')
def company_drives():
    return render_template(
        "company/drives.html",
        role="company",
        drives=[
            {
                "id": 1,
                "role": "Backend Developer",
                "ctc": 8,
                "deadline": "2026-03-20",
                "status": "Active"
            }
        ]
    )


@app.route("/my_drives")
@login_required(required_role='company')
def my_drives():
    return render_template(
        "company/my_drives.html",
        role="company",
        stats={
            "total_drives": 5,
            "active_drives": 2,
            "total_applicants": 120,
            "shortlisted": 35,
            "students_placed": 15
        },
        active_drives=[
            {
                "id": 1,
                "role": "Backend Developer",
                "ctc": 8,
                "deadline": "2026-03-20",
                "status": "Active",
                "company": "Test Company",
                "location": "Mumbai, India",
                "applicants": 45,
                "shortlisted": 12,
                "placed": 8,
                "date": "2026-03-01",
                "time": "10:00 AM"
            }
        ],
        completed_drives=[
            {
                "id": 2,
                "role": "Frontend Developer",
                "ctc": 10,
                "deadline": "2026-02-15",
                "status": "Inactive",
                "company": "Test Company",
                "location": "Mumbai, India",
                "applicants": 32,
                "shortlisted": 8,
                "placed": 5,
                "date": "2026-02-01",
                "time": "10:00 AM"
            }
        ]
    )


@app.route("/company/restart-drive/<int:drive_id>")
@login_required(required_role='company')
def restart_drive(drive_id):
    return f"""
    <h2>Drive {drive_id} Restarted Successfully</h2>
    <a href='/my_drives'>Back to My Drives</a>
    """


@app.route("/company/cancel-drive/<int:drive_id>")
@login_required(required_role='company')
def cancel_drive(drive_id):
    return f"""
    <h2>Drive {drive_id} Cancelled Successfully</h2>
    <a href='/my_drives'>Back to My Drives</a>
    """


@app.route("/create-drive")
@login_required(required_role='company')
def create_drive():
    return render_template(
        "company/create_drive.html",
        role="company",
        form_data={}
    )

@app.route("/company/view-drive/<int:drive_id>")
@login_required(required_role='company')
def view_drive(drive_id):
    return render_template(
        "company/view_drive.html",
        role="company",
        drive={
            "id": drive_id,
            "role": "Backend Developer",
            "company": "Test Company",
            "location": "Mumbai, India",
            "applicants": 45,
            "shortlisted": 12,
            "placed": 8
        },
        applicants=[
            {
                "id": 1,
                "name": "John Doe",
                "avatar": "/static/avatar1.jpg",
                "branch": "Computer Engineering",
                "status": "Shortlisted",
                "applied_date": "2026-03-01",
                "resume": "/static/resume1.pdf",
                "cover_letter": "/static/cover_letter1.pdf"
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "avatar": "/static/avatar2.jpg",
                "branch": "Information Technology",
                "status": "Placed",
                "applied_date": "2026-02-15",
                "resume": "/static/resume2.pdf",
                "cover_letter": "/static/cover_letter2.pdf"
            }
        ]
    )

@app.route("/company/edit-drive/<int:drive_id>")
@login_required(required_role='company')
def edit_drive(drive_id):
    return render_template(
        "company/edit_drive.html",
        role="company",
        drive={
            "id": drive_id,
            "role": "Backend Developer",
            "ctc": 8,
            "deadline": "2026-03-20",
            "description": "Drive description here."
        }
    )

@app.route("/company/applications")
@login_required(required_role='company')
def company_applications():
    return render_template(
        "company/applications.html",
        role="company",
        applications=[
            {
                "student": "Test Student",
                "role": "Backend Developer",
                "status": "Shortlisted",
                "date": "2026-03-02"
            }
        ]
    )

@app.route("/applicants")
@login_required(required_role='company')
def applicants():
    return render_template(
        "company/applications.html",
        role="company",
        applications=[
            {
                "student": "Test Student",
                "role": "Backend Developer",
                "status": "Shortlisted",
                "date": "2026-03-02"
            }
        ]
    )

@app.route("/company/profile")
@login_required(required_role='company')
def company_profile():
    return render_template(
        "company/profile.html",
        role="company",
        company={
            "name": "Test Company",
            "industry": "Technology",
            "email": "hr@testcompany.com",
            "website": "https://company.com",
            "description": "Company description here."
        }
    )

@app.route("/company_profile")
@login_required(required_role='company')
def company_profile_alt():
    return render_template(
        "company/profile.html",
        role="company",
        company={
            "name": "Test Company",
            "industry": "Technology",
            "email": "hr@testcompany.com",
            "website": "https://company.com",
            "description": "Company description here."
        }
    )

@app.route("/notifications")
@login_required(required_role='company')
def notifications():
    return render_template(
        "company/notifications.html",
        role="company",
        notifications=[]
    )

@app.route("/settings")
@login_required(required_role='company')
def settings():
    return render_template(
        "company/settings.html",
        role="company"
    )

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html', selected_role='student')

    email    = request.form.get('email')
    password = request.form.get('password')
    role     = request.form.get('role')

    try:
        response = requests.post('http://localhost:5000/api/auth/login', json={
            'email':    email,
            'password': password,
            'role':     role
        })
        data = response.json()

        if response.status_code == 200:
            resp = make_response(redirect(url_for(f'{role}_dashboard')))
            resp.set_cookie('jwt_token', data['token'], httponly=True)
            resp.set_cookie('role', role, httponly=True)
            resp.set_cookie('user_name', data['name'], httponly=True)
            return resp
        else:
            flash(data.get('message', 'Login failed'), 'error')
            return render_template('auth/login.html',
                                   selected_role=role,
                                   form_email=email)
    except:
        flash('Cannot connect to server. Try again later.', 'error')
        return render_template('auth/login.html', selected_role=role)

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html', selected_role='student')

    name             = request.form.get('name')
    email            = request.form.get('email')
    password         = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    role             = request.form.get('role')

    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return render_template('auth/register.html',
                               selected_role=role,
                               form_name=name,
                               form_email=email)

    try:
        response = requests.post('http://localhost:5000/api/auth/register', json={
            'name':     name,
            'email':    email,
            'password': password,
            'role':     role
        })
        data = response.json()

        if response.status_code == 201:
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(data.get('message', 'Registration failed'), 'error')
            return render_template('auth/register.html',
                                   selected_role=role,
                                   form_name=name,
                                   form_email=email)
    except:
        flash('Cannot connect to server. Try again later.', 'error')
        return render_template('auth/register.html', selected_role=role)


# LOGOUT
@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('jwt_token')
    resp.delete_cookie('role')
    resp.delete_cookie('user_name')
    return resp

if __name__ == "__main__":
    app.run(debug=True, port=5001)