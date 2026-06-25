"""
Database Seeding Script
"""
from backend.app import create_app
from backend.models import db, User, Student, Company, PlacementDrive, UserRole
from datetime import datetime, timedelta

app = create_app('development')

with app.app_context():
    # Clear existing data (comment out to preserve data)
    # db.drop_all()
    # db.create_all()
    
    print('🌱 Starting database seeding...')
    
    # Create Admin (only if doesn't exist)
    admin = User.query.filter_by(email='admin@placement.com').first()
    if not admin:
        admin = User(name='Admin', email='admin@placement.com', role=UserRole.ADMIN)
        admin.set_password('admin123')
        db.session.add(admin)
        print('✅ Admin created')
    
    # Create Test Students
    students_data = [
        {'name': 'Rahul Kumar', 'email': 'rahul@student.com', 'branch': 'CS', 'year': 'Final', 'cgpa': 8.5},
        {'name': 'Priya Singh', 'email': 'priya@student.com', 'branch': 'IT', 'year': 'Final', 'cgpa': 8.2},
        {'name': 'Amit Patel', 'email': 'amit@student.com', 'branch': 'CS', 'year': '3rd', 'cgpa': 7.8},
        {'name': 'Neha Sharma', 'email': 'neha@student.com', 'branch': 'IT', 'year': '3rd', 'cgpa': 9.0},
        {'name': 'Rohan Verma', 'email': 'rohan@student.com', 'branch': 'ENTC', 'year': 'Final', 'cgpa': 7.5},
    ]
    
    for data in students_data:
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            user = User(name=data['name'], email=data['email'], role=UserRole.STUDENT, is_active=True)
            user.set_password('student123')
            db.session.add(user)
            db.session.flush()
            
            student = Student(
                user_id=user.id,
                branch=data['branch'],
                year=data['year'],
                cgpa=data['cgpa'],
                phone='9876543210',
                address='Mumbai, India'
            )
            db.session.add(student)
            print(f'✅ Student created: {data["name"]}')
    
    # Create Test Companies
    companies_data = [
        {'name': 'TCS', 'email': 'hr@tcs.com', 'industry': 'IT Services', 'location': 'Mumbai'},
        {'name': 'Infosys', 'email': 'hr@infosys.com', 'industry': 'IT Services', 'location': 'Pune'},
        {'name': 'Amazon', 'email': 'hr@amazon.com', 'industry': 'Technology', 'location': 'Bangalore'},
        {'name': 'Wipro', 'email': 'hr@wipro.com', 'industry': 'IT Services', 'location': 'Bangalore'},
        {'name': 'Microsoft', 'email': 'hr@microsoft.com', 'industry': 'Technology', 'location': 'Hyderabad'},
    ]
    
    for data in companies_data:
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            user = User(name=data['name'], email=data['email'], role=UserRole.COMPANY, is_active=True)
            user.set_password('company123')
            db.session.add(user)
            db.session.flush()
            
            company = Company(
                user_id=user.id,
                company_name=data['name'],
                industry=data['industry'],
                location=data['location'],
                phone='+91-1234567890',
                website=f'https://{data["name"].lower()}.com',
                description=f'{data["name"]} is a leading {data["industry"]} company.',
                approval_status='approved'  # Pre-approve for testing
            )
            db.session.add(company)
            print(f'✅ Company created: {data["name"]}')
    
    db.session.commit()
    
    # Create Test Placement Drives
    print('\n📋 Creating placement drives...')
    
    companies = Company.query.all()
    for i, company in enumerate(companies):
        # Create 2 drives per company
        for j in range(2):
            drive_name = f'Software Engineer' if j == 0 else f'Backend Developer'
            
            existing_drive = PlacementDrive.query.filter_by(
                company_id=company.id,
                job_title=drive_name
            ).first()
            
            if not existing_drive:
                drive = PlacementDrive(
                    company_id=company.id,
                    job_title=f'{drive_name} - {company.company_name}',
                    job_description=f'We are looking for talented {drive_name}s to join our team at {company.company_name}.',
                    location=company.location,
                    job_type='Full Time',
                    min_cgpa=7.0,
                    eligible_branches='CS,IT,ENTC',
                    eligible_years='3rd,Final',
                    salary_min=6.0 + j,
                    salary_max=10.0 + j,
                    application_deadline=datetime.utcnow() + timedelta(days=30 + j*7),
                    status='approved'  # Pre-approve for testing
                )
                db.session.add(drive)
                print(f'✅ Drive created: {drive.job_title}')
    
    db.session.commit()
    
    print('\n✨ Database seeding completed successfully!')
    print('\n📚 Test Accounts:')
    print('  Admin: admin@placement.com / admin123')
    print('  Students: rahul@student.com, priya@student.com / student123')
    print('  Companies: hr@tcs.com, hr@infosys.com / company123')