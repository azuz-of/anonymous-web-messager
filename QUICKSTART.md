# Quick Start Guide

## Step 1: Backend Setup

### 1.1 Activate Virtual Environment (if not already active)
```bash
cd /Users/user/Desktop/Projects/secret-app
source venv/bin/activate
```

### 1.2 Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 1.3 Create Database Migrations
```bash
python manage.py makemigrations messenger
```

### 1.4 Run Migrations
```bash
python manage.py migrate
```

### 1.5 Create Admin User (Optional - for admin panel)
```bash
python manage.py createsuperuser
```
Follow the prompts to create a username, email, and password.

### 1.6 Run Backend Server

**Option A: Standard Django Server (for testing, but WebSockets won't work)**
```bash
python manage.py runserver
```

**Option B: ASGI Server (Recommended - supports WebSockets)**
```bash
pip install daphne
# For localhost only:
daphne -b 127.0.0.1 -p 8000 config.asgi:application

# For network access (accessible from other devices):
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

The backend will be available at `http://localhost:8000`

## Step 2: Frontend Setup

### 2.1 Navigate to Frontend Directory
Open a **new terminal window** and run:
```bash
cd /Users/user/Desktop/Projects/secret-app/frontend
```

### 2.2 Install Node Dependencies
```bash
npm install
```

### 2.3 Run Frontend Development Server
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Step 3: Access the Application

1. Open your browser and go to: `http://localhost:3000`
2. Enter a nickname to create a session
3. Create a room or join with a room code
4. Start chatting!

## Admin Panel

Access the admin panel at: `http://localhost:8000/admin/`
Use the superuser credentials you created in step 1.5

## Troubleshooting

### If you get "Module not found" errors:
- Make sure the virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### If WebSockets don't work:
- Make sure you're using Daphne (Option B in step 1.6)
- Check that the frontend proxy is configured correctly in `vite.config.js`

### If frontend can't connect to backend:
- Make sure backend is running on port 8000
- Check CORS settings in `config/settings.py`
- Verify the proxy configuration in `frontend/vite.config.js`

### If you see database errors:
- Run migrations: `python manage.py migrate`
- If tables don't exist, run: `python manage.py makemigrations messenger` then `python manage.py migrate`
