# Complete Setup Guide - Placement Application Portal

This guide provides step-by-step instructions to set up and run the Placement Application Portal with all its components: Backend, Frontend, Redis, and Celery.

## 📋 System Requirements

### Minimum Requirements
- **Operating System**: Linux, macOS, or Windows
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for package installation

### Software Prerequisites
- **Python 3.8 or higher**
- **Node.js 16 or higher**
- **Redis Server**
- **Git**

## 🔧 Installation Steps

### Step 1: Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm redis-server git
```

#### macOS (using Homebrew)
```bash
brew install python3 node redis git
```

#### Windows
1. Download and install Python 3.8+ from [python.org](https://python.org)
2. Download and install Node.js 16+ from [nodejs.org](https://nodejs.org)
3. Download and install Redis from [redis.io](https://redis.io/download)
4. Install Git from [git-scm.com](https://git-scm.com)

### Step 2: Clone the Repository

```bash
git clone https://github.com/gdgvitpune/placement-application-portal.git
cd placement-application-portal
```

### Step 3: Environment Configuration

```bash
# Copy the environment template
cp .env.example .env

# Edit the .env file with your settings
nano .env  # or use any text editor
```

**Required .env configuration:**
```bash
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///placement.db

# Email Configuration (optional - for notifications)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🚀 Backend Setup

### Step 1: Navigate to Backend Directory
```bash
cd backend
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database
```bash
# Seed the database with test data
python seed_db.py
```

### Step 5: Run Database Migration
```bash
# Add new database fields for company and drive details
python migrate_db.py
```
**Expected Output:**
```
Adding database fields for company and drive details...
Added industry column to companies table
Added location column to companies table
Added employees column to companies table
Added description column to companies table
Added rating column to companies table
Added job_type column to placement_drives table
Added ctc column to placement_drives table
Added drive_location column to placement_drives table
Database migration completed successfully!
Company and drive details integration is now complete!
```

### Step 6: Start Backend Server
```bash
python app.py
```

**Expected Output:**
```
* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## 🎨 Frontend Setup

### Step 1: Open New Terminal
```bash
# From project root (not backend directory)
cd frontend
```

### Step 2: Install Dependencies
```bash
npm install
```

### Step 3: Start Development Server
```bash
npm run dev
```

**Expected Output:**
```
VITE v7.3.1  ready in 332 ms
➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

## 🔄 Redis Setup

### Step 1: Start Redis Server
```bash
# Linux/macOS
redis-server

# Windows (if installed as service)
net start redis
```

**Expected Output:**
```
* Ready to accept connections
```

### Step 2: Verify Redis is Running
```bash
redis-cli ping
```
**Expected Response:** `PONG`

## ⚙️ Celery Setup

### Step 1: Start Celery Worker (Terminal 1)
```bash
cd backend
celery -A celery_worker.celery worker --loglevel=info
```

**Expected Output:**
```
[2024-01-01 12:00:00,000: INFO/MainProcess] celery@hostname ready.
```

### Step 2: Start Celery Beat (Terminal 2)
```bash
cd backend
celery -A celery_worker.celery beat --loglevel=info
```

**Expected Output:**
```
[2024-01-01 12:00:00,000: INFO/MainProcess] Scheduler started.
```

## 🌐 Access the Application

Once all services are running, access the application at:

- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000 (Flask-RESTX docs)

## 🔐 Test Login Credentials

### Admin Account
- **Email**: admin@placement.com
- **Password**: admin123
- **Role**: admin

### Company Accounts
- **TCS HR**
  - Email: hr@tcs.com
  - Password: company123
  - Role: company

- **Infosys HR**
  - Email: hr@infosys.com
  - Password: company123
  - Role: company

### Student Accounts
- **Rahul Kumar**
  - Email: rahul@student.com
  - Password: student123
  - Role: student

- **Priya Singh**
  - Email: priya@student.com
  - Password: student123
  - Role: student

## 📊 Verification Steps

### 1. Test Backend API
```bash
curl http://localhost:5000/api/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@placement.com","password":"admin123","role":"admin"}'
```

### 2. Test Frontend
Open http://localhost:5173 in your browser and try logging in with test credentials.

### 3. Test Celery Tasks
```bash
# Check Celery worker status
celery -A backend.celery_worker.celery status
```

## 🛠️ Development Workflow

### Starting All Services (Recommended Order)

1. **Terminal 1**: Redis Server
   ```bash
   redis-server
   ```

2. **Terminal 2**: Backend Server
   ```bash
   cd backend
   source venv/bin/activate
   python app.py
   ```

3. **Terminal 3**: Run Database Migration (First time only)
   ```bash
   cd backend
   source venv/bin/activate
   python migrate_db.py
   ```

4. **Terminal 4**: Celery Worker
   ```bash
   cd backend
   source venv/bin/activate
   celery -A celery_worker.celery worker --loglevel=info
   ```

5. **Terminal 5**: Celery Beat
   ```bash
   cd backend
   source venv/bin/activate
   celery -A celery_worker.celery beat --loglevel=info
   ```

6. **Terminal 6**: Frontend Server
   ```bash
   cd frontend
   npm run dev
   ```

### Stopping All Services
```bash
# Find and kill processes
pkill -f "python app.py"
pkill -f "celery"
pkill -f "redis-server"
pkill -f "npm"
```

## 🔧 Troubleshooting

### Backend Issues

#### Port 5000 Already in Use
```bash
# Find process using port 5000
lsof -i :5000
# Kill the process
kill -9 <PID>
```

#### Database Issues
```bash
cd backend
rm instance/placement.db
python seed_db.py
python migrate_db.py  # Run migration after database reset
```

#### Import Errors
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

#### Port 5173 Already in Use
```bash
lsof -i :5173
kill -9 <PID>
```

#### Build Errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Redis Issues

#### Connection Refused
```bash
# Start Redis
redis-server

# Or check if Redis is running
redis-cli ping
```

#### Permission Denied
```bash
# On Linux/macOS
sudo redis-server
```

### Celery Issues

#### Worker Not Starting
```bash
cd backend
source venv/bin/activate
celery -A celery_worker.celery worker --loglevel=debug
```

#### Tasks Not Running
```bash
# Check Redis connection
redis-cli -n 0 keys "*"
```

## 📧 Email Configuration (Optional)

### Gmail Setup
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Add to `.env`:
   ```bash
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-character-app-password
   ```

### Testing Email
```bash
cd backend
source venv/bin/activate
python -c "
from app import mail
from flask_mail import Message
msg = Message('Test', recipients=['test@example.com'], body='Test email')
mail.send(msg)
print('Email sent!')
"
```

## 🔄 Updating the Application

### Backend Updates
```bash
cd backend
source venv/bin/activate
git pull
pip install -r requirements.txt
python seed_db.py  # If database schema changed
python migrate_db.py  # Run database migration for new fields
```

### Frontend Updates
```bash
cd frontend
git pull
npm install
```

## 📝 Production Deployment

### Environment Variables for Production
```bash
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:password@localhost/placement_db
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
MAIL_USERNAME=your-production-email@domain.com
MAIL_PASSWORD=your-production-email-password
```

### Using Process Managers

#### PM2 for Node.js (Frontend)
```bash
npm install -g pm2
cd frontend
pm2 start "npm run build && npm run preview" --name placement-frontend
```

#### Gunicorn for Flask (Backend)
```bash
pip install gunicorn
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Supervisor for Celery
```bash
pip install supervisor
# Configure supervisor for Celery worker and beat
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Ensure all services are running in the correct order
4. Check logs for error messages
5. Open an issue on the GitHub repository

## 🎯 Next Steps

Once everything is running:

1. **Explore the Admin Dashboard** - View system statistics
2. **Test Company Features** - Create placement drives, schedule interviews, finalize selections
3. **Test Student Features** - Browse and apply to drives, view company details
4. **Configure Email** - Set up notifications
5. **Customize** - Modify themes, add features

### New Features Added
- **Interview Scheduling** - Companies can schedule interviews for shortlisted candidates
- **Final Selection** - Companies can finalize hiring decisions with remarks
- **Enhanced Company Details** - Students can view comprehensive company information
- **Real-time Dashboard Sync** - All three dashboards (Student, Admin, Company) are synchronized

Happy coding! 🚀