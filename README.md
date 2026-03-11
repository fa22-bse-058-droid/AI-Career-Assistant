# 🤖 AI-Powered Career Assistant Platform

A production-ready full-stack web application built as a Final Year Project at **COMSATS University Islamabad (Sahiwal Campus)**.

## 🏗️ Architecture

```
.
├── backend/           # Django 4.2 + DRF + Channels
│   ├── career_platform/   # Core settings, celery, urls
│   └── apps/
│       ├── authentication/   # Module 1: JWT, RBAC, lockout
│       ├── cv_analyzer/      # Module 2: CV upload + AI scoring
│       ├── jobs/             # Module 3: Scraper + MiniLM matching
│       ├── chatbot/          # Module 4: WebSocket + BlenderBot
│       ├── resources/        # Module 5: Personalized resources
│       ├── forum/            # Module 6: Forum + gamification
│       ├── auto_apply/       # Module 7: Celery auto-apply pipeline
│       ├── notifications/    # Module 8: Email + on-site alerts
│       ├── admin_panel/      # Module 9: Admin RBAC panel
│       └── mock_interview/   # Module 10: AI interview evaluation
├── frontend/          # React 18 + TypeScript + Vite
│   └── src/
│       ├── pages/     # All 10 module pages
│       ├── components/ # Reusable UI components
│       ├── store/     # Zustand auth store
│       └── api/       # Axios + JWT interceptor
├── fastapi_service/   # FastAPI AI inference microservice
├── nginx/             # Nginx reverse proxy config
└── docker-compose.yml # Full stack orchestration
```

## 🚀 Tech Stack

### Backend
- **Python 3.11** + **Django 4.2** + **Django REST Framework**
- **FastAPI** (AI inference microservice on port 8001)
- **MySQL 8** (primary database)
- **Redis 7** (caching + Celery broker + Channels layer)
- **Celery 5** + **Celery Beat** (async tasks + scheduling)
- **Django Channels 4** + **Daphne** (WebSocket for chatbot)
- **JWT** via `djangorestframework-simplejwt` (60min access, rotating refresh)

### AI/ML
- **spaCy** `en_core_web_sm` — NER for CV text processing
- **sentence-transformers** `all-MiniLM-L6-v2` — job matching cosine similarity
- **Hugging Face** `facebook/blenderbot-400M-distill` — AI chatbot
- CV scoring: 30% keyword relevance + 25% completeness + 25% skill density + 20% formatting

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **TailwindCSS 3** with dark glassmorphism design
- **Framer Motion** (all animations)
- **Zustand** (global state) + **React Query** (server state)
- **Axios** with JWT interceptor + refresh token rotation

### Infrastructure
- **Docker Compose** (8 services: django, react, mysql, redis, celery_worker, celery_beat, flower, nginx)
- **Nginx** reverse proxy + WebSocket proxy + gzip
- **Flower** (Celery monitoring UI on port 5555)

## 📦 10 Modules

| # | Module | Key Features |
|---|--------|-------------|
| 1 | Authentication | JWT, RBAC (Student/Employer/Admin), account lockout, profile |
| 2 | CV Analyzer | PDF/DOCX upload, skill extraction, 4-factor scoring, skill gap detection |
| 3 | Job Board | Rozee.pk + Indeed + LinkedIn scraper, MiniLM semantic matching |
| 4 | AI Chatbot | WebSocket, BlenderBot, multi-turn context, conversation history |
| 5 | Resource Hub | Skill gap → course recommendations, card flip UI |
| 6 | Community Forum | Posts, threaded replies, gamification (points + badges) |
| 7 | Auto-Apply | Celery pipeline, daily quota, duplicate detection |
| 8 | Notifications | Email + on-site, weekly digest, preference controls |
| 9 | Admin Panel | RBAC, user management, scraper health, audit logs, CSV export |
| 10 | Mock Interview | 200+ questions, AI evaluation, adaptive follow-ups, PDF report |

## 🎨 Design System

- **Dark theme**: primary `#0A0F1E`, secondary `#0D1117`
- **Glassmorphism**: `backdrop-filter: blur(16px)`, semi-transparent borders
- **Gradient accents**: blue `#3B82F6` → purple `#8B5CF6` → cyan `#06B6D4`
- **Framer Motion**: page transitions, scroll reveals, hover interactions
- **Typography**: Inter font, large bold headings

## 🏁 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### Development Setup

```bash
# Copy environment file
cp backend/.env.example backend/.env
# Edit backend/.env with your values

# Start all services
docker-compose up -d

# Check services
docker-compose ps
```

### Manual Setup (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# In separate terminals:
celery -A career_platform worker --loglevel=info
celery -A career_platform beat --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v --cov=apps
```

## 📡 Key API Endpoints

| Module | Endpoint | Methods |
|--------|----------|---------|
| Auth | `/api/auth/register/` | POST |
| Auth | `/api/auth/login/` | POST |
| Auth | `/api/auth/me/` | GET, PATCH |
| CV | `/api/cv/upload/` | POST |
| CV | `/api/cv/<id>/status/` | GET |
| Jobs | `/api/jobs/` | GET |
| Jobs | `/api/jobs/matches/` | GET |
| Chat | `/api/chat/conversations/` | GET, POST |
| Forum | `/api/forum/posts/` | GET, POST |
| Forum | `/api/forum/leaderboard/` | GET |
| Interview | `/api/interview/sessions/start/` | POST |
| Admin | `/api/admin-panel/stats/` | GET |

**WebSocket**: `ws://localhost/ws/chat/?token=<access_token>`

## 🔐 Security

- Rate limiting: login 5/min, register 3/min, CV upload 10/hr
- Account lockout: 5 failed attempts → 15 min lock
- Magic byte validation for file uploads
- Input sanitization with `bleach` for forum HTML
- JWT with rotating refresh tokens
- CSP headers via `django-csp`
- All secrets in `.env` (never hardcoded)

---

*Built by FA22-BSE-058 @ COMSATS University Islamabad (Sahiwal Campus)*