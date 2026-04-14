# AI Career Assistant — Local Setup (No Docker)

This project runs fully **without Docker**.  
All code and data live at **`D:\AI-Career-Assistant`** (Windows) / **`/mnt/d/AI-Career-Assistant`** (WSL2).

## Project Structure

```
D:\AI-Career-Assistant\
├── backend\          Django + DRF + Celery (port 8000)
├── fastapi_service\  FastAPI AI service    (port 8001)
├── frontend\         React + Vite          (port 5173)
├── nginx\            legacy config — not needed for local dev
├── start-local.bat   one-click Windows launcher
└── start-local.sh    one-click WSL2 launcher
```

---

## Prerequisites

Install the following before running the project.

| Tool | Minimum version | Download |
|------|----------------|---------|
| Python | **3.11** | https://www.python.org/downloads/ |
| Node.js (LTS) | **18** | https://nodejs.org/ |
| MySQL | **8.0** | https://dev.mysql.com/downloads/installer/ |
| Redis | **7** | see section 2 below |
| pip | ships with Python 3.11 | — |
| npm | ships with Node 18 | — |

> **WSL2 users:** install Python and Node inside WSL2 (Ubuntu).  
> MySQL and Redis can run as Windows services and are reachable from WSL2 via `localhost`.

---

## 1) MySQL 8.0 — Installation and Database Setup

### Option A — Windows (PowerShell as Administrator)

```powershell
winget install -e --id Oracle.MySQL
net start MySQL80
```

### Option B — WSL2 (Ubuntu terminal)

```bash
sudo apt update
sudo apt install -y mysql-server
sudo service mysql start
```

### Create the database and user

Run from either a PowerShell or WSL2 terminal:

```bash
mysql -u root -p
```

Then execute:

```sql
CREATE DATABASE career_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'career_user'@'localhost' IDENTIFIED BY 'career_password';
GRANT ALL PRIVILEGES ON career_platform.* TO 'career_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 2) Redis — Installation

### Option A — Windows (PowerShell as Administrator)

```powershell
choco install redis-64 -y
redis-server --service-install
redis-server --service-start
```

### Option B — WSL2 (Ubuntu terminal)

```bash
sudo apt update
sudo apt install -y redis-server
sudo service redis-server start
```

### Verify Redis is running

```bash
redis-cli ping
```

Expected output:

```
PONG
```

---

## 3) Python Virtual Environment + Backend Dependencies

**Windows (PowerShell):**

```powershell
cd D:\AI-Career-Assistant
python -m venv backend\.venv
backend\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
pip install -r fastapi_service\requirements.txt
python -m spacy download en_core_web_sm
```

**WSL2 (Ubuntu terminal):**

```bash
cd /mnt/d/AI-Career-Assistant
python3.11 -m venv backend/.venv
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r fastapi_service/requirements.txt
python -m spacy download en_core_web_sm
```

> The same virtual environment is shared by the Django backend, Celery, and the FastAPI service.

### Backend dependencies at a glance

| Package | Purpose |
|---------|---------|
| Django 4.2 + DRF | web framework + REST API |
| djangorestframework-simplejwt | JWT authentication |
| channels + channels-redis | WebSocket / real-time |
| celery[redis] + django-celery-beat | async task queue + scheduled jobs |
| mysqlclient 2.2 | MySQL driver |
| redis 5 | Redis client |
| spacy + sentence-transformers + torch | AI / NLP features |
| PyPDF2, python-docx, pdfminer | CV / document parsing |
| selenium + webdriver-manager | job scraping |

---

## 4) Frontend Dependencies

**Windows (PowerShell):**

```powershell
cd D:\AI-Career-Assistant\frontend
npm install
```

**WSL2:**

```bash
cd /mnt/d/AI-Career-Assistant/frontend
npm install
```

### Frontend dependencies at a glance

| Package | Purpose |
|---------|---------|
| React 18 + Vite 5 | UI framework + build tool |
| TypeScript 5 | static typing |
| Tailwind CSS 3 | utility-first styling |
| React Router 6 | client-side routing |
| Axios 1.7 | HTTP client |
| Zustand 5 | global state |
| React Hook Form + Zod | forms + validation |
| Socket.io-client | real-time updates |
| TanStack Query 5 | server-state / caching |

---

## 5) FastAPI Service Dependencies

The FastAPI service shares the same virtual environment created in step 3 (`backend/.venv`).  
Its own `fastapi_service/requirements.txt` lists:

| Package | Purpose |
|---------|---------|
| fastapi 0.115 + uvicorn | API framework + ASGI server |
| sentence-transformers + transformers | NLP embeddings |
| torch (CPU build) | ML inference |
| pydantic 2 | data validation |

---

## 6) Environment Variables

### Backend

**Windows:**
```powershell
copy D:\AI-Career-Assistant\backend\.env.example D:\AI-Career-Assistant\backend\.env
```

**WSL2:**
```bash
cp /mnt/d/AI-Career-Assistant/backend/.env.example /mnt/d/AI-Career-Assistant/backend/.env
```

Edit `backend/.env` and set these values for local development:

```env
SECRET_KEY=your-super-secret-key-at-least-32-chars-long
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL (matches the database you created in step 1)
DB_NAME=career_platform
DB_USER=career_user
DB_PASSWORD=career_password
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS — allow the Vite dev server
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# FastAPI AI service
AI_SERVICE_URL=http://localhost:8001

# Email — use Mailtrap (https://mailtrap.io) or console backend for local dev
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

LOG_LEVEL=INFO
```

> Use `backend/.env.example` as the authoritative template — it is kept up to date.

### Frontend

**Windows:**
```powershell
copy D:\AI-Career-Assistant\frontend\.env.example D:\AI-Career-Assistant\frontend\.env
```

**WSL2:**
```bash
cp /mnt/d/AI-Career-Assistant/frontend/.env.example /mnt/d/AI-Career-Assistant/frontend/.env
```

The default values in `frontend/.env.example` work out of the box for local development:

```env
VITE_API_URL=/api
VITE_WS_URL=ws://localhost/ws
```

---

## 7) Run Everything Locally

Open **5 separate terminals** (PowerShell or WSL2 — be consistent within a session).

### Terminal 1 — Django (port 8000)

**Windows:**
```powershell
cd D:\AI-Career-Assistant\backend
.\.venv\Scripts\activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

**WSL2:**
```bash
cd /mnt/d/AI-Career-Assistant/backend
source .venv/bin/activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2 — Celery Worker

> **Windows note:** Celery requires `--pool=solo` on Windows because it does not support the default `prefork` process pool. This also implies `--concurrency=1` (single-threaded worker).

**Windows:**
```powershell
cd D:\AI-Career-Assistant\backend
.\.venv\Scripts\activate
celery -A career_platform worker --loglevel=info --pool=solo
```

**WSL2:**
```bash
cd /mnt/d/AI-Career-Assistant/backend
source .venv/bin/activate
celery -A career_platform worker --loglevel=info --concurrency=4
```

### Terminal 3 — Celery Beat

**Windows:**
```powershell
cd D:\AI-Career-Assistant\backend
.\.venv\Scripts\activate
celery -A career_platform beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**WSL2:**
```bash
cd /mnt/d/AI-Career-Assistant/backend
source .venv/bin/activate
celery -A career_platform beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Terminal 4 — FastAPI AI service (port 8001)

**Windows:**
```powershell
cd D:\AI-Career-Assistant\fastapi_service
..\backend\.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**WSL2:**
```bash
cd /mnt/d/AI-Career-Assistant/fastapi_service
source ../backend/.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Terminal 5 — React dev server (port 5173)

**Windows:**
```powershell
cd D:\AI-Career-Assistant\frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

**WSL2:**
```bash
cd /mnt/d/AI-Career-Assistant/frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

### App URLs

| Service | URL |
|---------|-----|
| Frontend (React) | http://localhost:5173 |
| Django REST API | http://localhost:8000/api/ |
| Django admin | http://localhost:8000/admin/ |
| FastAPI AI service | http://localhost:8001 |
| FastAPI docs | http://localhost:8001/docs |

---

## 8) One-Click Startup

### Windows — `start-local.bat`

Run from the repository root in PowerShell or Command Prompt:

```powershell
cd D:\AI-Career-Assistant
start-local.bat
```

This opens 5 separate windows (Django, Celery Worker, Celery Beat, FastAPI, React).

> Requires the virtual environment at `D:\AI-Career-Assistant\backend\.venv` to already exist (step 3).

### WSL2 — `start-local.sh`

Run from the repository root in a WSL2 terminal:

```bash
cd /mnt/d/AI-Career-Assistant
bash start-local.sh
```

This starts all 5 services in the background and tails their combined log.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `celery` crashes on Windows with `can't pickle ...` | Use `--pool=solo` (already in `start-local.bat`) |
| `mysqlclient` install fails on Windows | Install [MySQL C connector](https://dev.mysql.com/downloads/connector/c/) first, or use WSL2 |
| `torch` install is slow / fails | Use the CPU-only wheel: `pip install torch==2.4.1+cpu --index-url https://download.pytorch.org/whl/cpu` |
| `redis-cli ping` returns `Could not connect` | Ensure `redis-server` service is running (step 2) |
| Port 8000/5173 already in use | Kill the process occupying it or change the port |
| `Access denied for user 'career_user'@'localhost'` | Re-run the SQL in step 1 to recreate the user and privileges |
