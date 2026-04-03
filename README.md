# AI Career Assistant (Local Setup)

This project now runs fully **without Docker**.

## Project Structure

- `backend/` — Django + DRF + Celery
- `frontend/` — React + Vite
- `fastapi_service/` — FastAPI AI service
- `nginx/` — legacy reverse-proxy config (not required for local run)

---

## 1) MySQL 8.0 Installation and Database Setup (Windows)

### Install MySQL 8.0

```powershell
winget install -e --id Oracle.MySQL
```

### Start MySQL service

```powershell
net start MySQL80
```

### Create database and user

```powershell
mysql -u root -p
```

Then run:

```sql
CREATE DATABASE career_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'career_user'@'localhost' IDENTIFIED BY 'career_password';
GRANT ALL PRIVILEGES ON career_platform.* TO 'career_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 2) Redis Installation on Windows

Install Redis (Windows package) with Chocolatey:

```powershell
choco install redis-64 -y
```

Start Redis service:

```powershell
redis-server --service-install
redis-server --service-start
```

Verify:

```powershell
redis-cli ping
```

Expected output:

```text
PONG
```

---

## 3) Python Virtual Environment Setup + Pip Install Commands

From repository root (`<PROJECT_ROOT>`):

```powershell
cd <PROJECT_ROOT>
python -m venv backend\.venv
backend\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
pip install -r fastapi_service\requirements.txt
python -m spacy download en_core_web_sm
```

---

## 4) Frontend Install

```powershell
cd <PROJECT_ROOT>\frontend
npm install
```

---

## 5) Environment Variables Setup

Create backend env file:

```powershell
copy backend\.env.example backend\.env
```

Use these local values in `backend/.env`:

```env
SECRET_KEY=your-super-secret-key-at-least-32-chars-long
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=career_platform
DB_USER=career_user
DB_PASSWORD=career_password
DB_HOST=localhost
DB_PORT=3306

REDIS_URL=redis://localhost:6379/0
AI_SERVICE_URL=http://localhost:8001
```

Frontend env:

```powershell
copy frontend\.env.example frontend\.env
```

---

## 6) Run Everything Locally (Django + Celery Worker + Celery Beat + FastAPI + React)

Open separate terminals.

### Terminal 1 — Django

```powershell
cd <PROJECT_ROOT>\backend
.\.venv\Scripts\activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2 — Celery Worker

```powershell
cd <PROJECT_ROOT>\backend
.\.venv\Scripts\activate
celery -A career_platform worker --loglevel=info --concurrency=4
```

### Terminal 3 — Celery Beat

```powershell
cd <PROJECT_ROOT>\backend
.\.venv\Scripts\activate
celery -A career_platform beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Terminal 4 — FastAPI

```powershell
cd <PROJECT_ROOT>\fastapi_service
..\backend\.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Terminal 5 — React

```powershell
cd <PROJECT_ROOT>\frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

App URLs:

- Frontend: `http://localhost:5173`
- Django API: `http://localhost:8000/api/`
- FastAPI: `http://localhost:8001`

---

## 7) One-Click Startup

Use the included batch file from repository root:

```powershell
cd <PROJECT_ROOT>
start-local.bat
```
