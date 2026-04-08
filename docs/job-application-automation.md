# Job Application Automation Module

> **AI-Career-Assistant** — Comprehensive Module Guide

---

## Table of Contents

1. [Module Overview](#1-module-overview)
2. [Tech Stack](#2-tech-stack)
3. [End-to-End Workflow](#3-end-to-end-workflow)
4. [Architecture & Components](#4-architecture--components)
5. [Database Models](#5-database-models)
6. [Backend Services & API Endpoints](#6-backend-services--api-endpoints)
7. [Permission Gating](#7-permission-gating)
8. [Data Inputs & Outputs](#8-data-inputs--outputs)
9. [Celery Tasks & Scheduling](#9-celery-tasks--scheduling)
10. [Logging & Monitoring](#10-logging--monitoring)
11. [Security & Privacy](#11-security--privacy)
12. [Frontend Integration (Website UI)](#12-frontend-integration-website-ui)
13. [Integration Steps (From Scratch)](#13-integration-steps-from-scratch)
14. [Error Handling & Retry Logic](#14-error-handling--retry-logic)
15. [Extending the Module](#15-extending-the-module)

---

## 1. Module Overview

The **Job Application Automation** module allows authenticated student users to:

- Collect job listings automatically from multiple job boards (Rozee.pk, Indeed, LinkedIn, Remotive, WeWorkRemotely, Arbeitnow, RemoteOK).
- Match those listings against the user's CV skills via semantic + keyword scoring.
- Grant **explicit permission** for the system to auto-apply on their behalf.
- Configure rules: minimum match score, daily application cap, and target roles.
- View a full audit log of every application attempt.

The agent **never submits** an application unless:

1. `is_enabled = True` on the user's `AutoApplySettings`.
2. The job's match score ≥ `min_match_score`.
3. The daily `max_applications_per_day` quota has not been reached.
4. The job has not already been applied to within the last 30 days.

---

## 2. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend framework** | Django 4.x + Django REST Framework | API server, ORM, admin |
| **Task queue** | Celery 5.x | Async scraping, matching, auto-apply |
| **Message broker** | Redis | Celery broker & result backend |
| **Scheduler** | `django-celery-beat` | Periodic scrape & match tasks |
| **Scraping** | `requests`, `BeautifulSoup4`, `feedparser`, `fake-useragent` | Job board HTTP scraping |
| **AI matching** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Semantic CV ↔ job similarity |
| **Database** | MySQL 8 (production), SQLite (tests) | Persistent storage |
| **Auth** | `djangorestframework-simplejwt` | JWT access + httpOnly refresh cookie |
| **Frontend** | React 18 + Vite + TypeScript | Website UI |
| **HTTP client** | Axios (with `withCredentials: true`) | API calls from React |
| **Notifications** | Internal `notifications` app + optional email | User alerts |
| **Automation layer** | Playwright / Selenium (planned extension) | Form-fill & submission |

---

## 3. End-to-End Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER JOURNEY                                │
│                                                                 │
│  1. Register / Login ──► Upload CV ──► CV Analysis complete     │
│                                                                 │
│  2. Visit Auto-Apply page                                       │
│     ├─ Read terms & consent disclaimer                          │
│     ├─ Set target roles (e.g. "Python Developer")              │
│     ├─ Set min match score (default 60%)                        │
│     ├─ Set daily cap (default 5)                                │
│     └─ Toggle "Enable Auto-Apply" → POST /api/auto-apply/       │
│            settings/  { is_enabled: true, ... }                 │
│                                                                 │
│  3. Background: Celery Beat triggers scraping tasks             │
│     ├─ scrape_rozee / scrape_linkedin / ...                     │
│     └─ Jobs saved to JobListing table                           │
│                                                                 │
│  4. Background: compute_matches_for_user                        │
│     ├─ Encode user CV text with MiniLM                          │
│     ├─ Encode each active job                                   │
│     ├─ Combine semantic + keyword score                         │
│     └─ Save UserJobMatch rows (score, skill_overlap)            │
│                                                                 │
│  5. Background: run_auto_apply_for_all_users                    │
│     └─ For each user with is_enabled=True:                      │
│          run_auto_apply_for_user(user_id)                       │
│            ├─ Load AutoApplySettings                            │
│            ├─ Filter UserJobMatch rows ≥ min_match_score        │
│            ├─ Check daily quota (ApplicationLog count)          │
│            ├─ Skip if applied in last 30 days                   │
│            ├─ Submit application (log only; Playwright TBD)     │
│            ├─ Write ApplicationLog (applied/failed/skipped)     │
│            └─ Notify user via notifications app                 │
│                                                                 │
│  6. User views dashboard:                                       │
│     └─ GET /api/auto-apply/logs/  → application history        │
│                                                                 │
│  7. User revokes permission:                                    │
│     └─ PATCH /api/auto-apply/settings/ { is_enabled: false }   │
│        → Agent stops immediately on next cycle                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Flow (Ordered)

| Step | Actor | Action |
|---|---|---|
| 1 | User | Registers with `role = student` |
| 2 | User | Uploads CV via `/api/cv/upload/` |
| 3 | System (Celery) | Runs CV analysis; extracts skills → `CVAnalysis.extracted_skills` |
| 4 | System (Beat) | Scraping tasks run on schedule → populate `JobListing` |
| 5 | System (Celery) | `compute_matches_for_user` computes `UserJobMatch` scores |
| 6 | User | Opens **Auto-Apply** page; reads consent; configures settings |
| 7 | User | Enables auto-apply → `AutoApplySettings.is_enabled = True` |
| 8 | System (Beat) | `run_auto_apply_for_all_users` fires periodically |
| 9 | System (Celery) | For each enabled user: load settings → check quota → apply |
| 10 | System | Writes `ApplicationLog` for every attempt |
| 11 | System | Sends in-app notification per successful application |
| 12 | User | Reviews log at `/api/auto-apply/logs/` or on the UI |
| 13 | User | Optionally revokes permission at any time |

---

## 4. Architecture & Components

```
backend/
├── apps/
│   ├── auto_apply/               ← This module
│   │   ├── models.py             ← AutoApplySettings, ApplicationLog
│   │   ├── serializers.py        ← DRF serializers
│   │   ├── views.py              ← API views
│   │   ├── urls.py               ← URL routing
│   │   └── tasks.py              ← Celery tasks
│   │
│   ├── jobs/                     ← Job data layer
│   │   ├── models.py             ← JobListing, UserJobMatch, ScraperRun, ...
│   │   ├── tasks.py              ← Scrape & match tasks
│   │   ├── scrapers/
│   │   │   ├── base_scraper.py   ← Abstract BaseScraper
│   │   │   ├── rozee_scraper.py
│   │   │   ├── indeed_scraper.py
│   │   │   ├── linkedin_scraper.py
│   │   │   ├── remotive_scraper.py
│   │   │   ├── weworkremotely_scraper.py
│   │   │   ├── arbeitnow_scraper.py
│   │   │   └── remoteok_scraper.py
│   │   └── utils/matcher.py      ← batch_compute_matches()
│   │
│   ├── cv_analyzer/              ← CV upload & skills extraction
│   │   ├── models.py             ← CVUpload, CVAnalysis
│   │   └── tasks.py              ← CV analysis tasks
│   │
│   ├── authentication/           ← User auth & RBAC
│   │   ├── models.py             ← CustomUser, UserProfile
│   │   └── permissions.py        ← IsStudent, IsEmployer, IsAdmin
│   │
│   └── notifications/            ← In-app & email alerts
│       ├── models.py
│       └── tasks.py              ← create_notification task
│
frontend/
└── src/pages/AutoApplyPage.tsx   ← React UI for this module
```

---

## 5. Database Models

### `AutoApplySettings`

Stores each user's permission grant and rule configuration.

| Column | Type | Description |
|---|---|---|
| `user` | FK → `CustomUser` | One-to-one owner |
| `is_enabled` | BooleanField | **Master permission switch** |
| `min_match_score` | FloatField | Minimum score (0.0–1.0, default 0.60) |
| `max_applications_per_day` | IntegerField | Daily cap (default 5) |
| `target_roles` | JSONField | List of role keywords to target |

### `ApplicationLog`

Immutable audit record for every application attempt.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `user` | FK → `CustomUser` | Applicant |
| `job` | FK → `JobListing` | Target job |
| `applied_at` | DateTimeField | Timestamp (auto) |
| `method` | CharField | `"auto"` or `"manual"` |
| `status` | CharField | `applied` / `failed` / `skipped` |
| `error_message` | TextField | Failure reason (if any) |

### `JobListing` (jobs app)

Scraped job data stored for matching.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `title` / `company` | CharField | Job info |
| `location` | CharField | City or "Remote" |
| `job_type` | CharField | full_time, part_time, internship, remote, hybrid |
| `source` | CharField | rozee, indeed, linkedin, remotive, weworkremotely, arbeitnow, remote_ok |
| `url` | URLField (unique) | Canonical application link |
| `skills_required` | JSONField | Extracted skill tags |
| `is_active` / `is_remote` | BooleanField | Status flags |
| `expires_at` | DateTimeField | Auto-set 30 days after scrape |

### `UserJobMatch` (jobs app)

Computed similarity score linking user CV to job.

| Column | Type | Description |
|---|---|---|
| `user` | FK → `CustomUser` | Owner |
| `job` | FK → `JobListing` | Matched job |
| `score` | FloatField | Composite score (0.0–1.0) |
| `skill_overlap` | JSONField | Matched skill tags |
| `skill_overlap_count` | IntegerField | Count of overlapping skills |

---

## 6. Backend Services & API Endpoints

All endpoints are prefixed with `/api/auto-apply/`.

| Method | URL | View | Auth Required | Permission | Description |
|---|---|---|---|---|---|
| `GET` | `/api/auto-apply/settings/` | `AutoApplySettingsView` | ✅ | `IsStudent` | Retrieve current settings (creates defaults if none) |
| `PATCH` | `/api/auto-apply/settings/` | `AutoApplySettingsView` | ✅ | `IsStudent` | Update settings (enable/disable, rules) |
| `GET` | `/api/auto-apply/logs/` | `ApplicationLogListView` | ✅ | `IsAuthenticated` | List all application logs for the current user |
| `POST` | `/api/auto-apply/trigger/` | `TriggerAutoApplyView` | ✅ | `IsStudent` | Manually queue auto-apply Celery task for the current user |

### Related Job Endpoints

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/jobs/` | Browse all active job listings |
| `GET` | `/api/jobs/<uuid>/` | Job detail |
| `GET` | `/api/jobs/matches/` | CV-matched jobs for current user |
| `POST` | `/api/jobs/applications/` | Manually submit a job application |
| `GET` | `/api/jobs/applications/` | List user's manual applications |
| `POST` | `/api/jobs/<uuid>/save/` | Save a job to bookmarks |
| `GET` | `/api/jobs/saved/` | List saved jobs |
| `GET` | `/api/jobs/scraper-runs/` | Admin: list scraper run history |

### Related CV Endpoint

| Method | URL | Description |
|---|---|---|
| `POST` | `/api/cv/upload/` | Upload CV file (triggers analysis + match recompute) |

---

## 7. Permission Gating

### Authentication

All auto-apply endpoints require a valid JWT access token:

```http
Authorization: Bearer <access_token>
```

The frontend sends this automatically via the Axios instance
(`frontend/src/api/axios.ts`) which uses `withCredentials: true` for the
httpOnly refresh-cookie and includes the bearer token from the in-memory
Zustand auth store.

### Role-Based Access Control (RBAC)

| Permission Class | Role Required | Used On |
|---|---|---|
| `IsAuthenticated` | Any logged-in user | `ApplicationLogListView` |
| `IsStudent` | `role == "student"` | `AutoApplySettingsView`, `TriggerAutoApplyView` |

Employers and admins **cannot** enable auto-apply for themselves.
The `IsStudent` permission class is defined in
`apps/authentication/permissions.py`.

### Runtime Permission Check (Task Level)

Inside `run_auto_apply_for_user`, the task performs these guards in order:

```
1. Does CustomUser exist?           → abort if not
2. Does AutoApplySettings exist     → abort if not
   AND is_enabled == True?
3. Has daily quota been exhausted?  → abort if applied_today >= max_applications_per_day
4. Was this job applied to in the   → log as "skipped" and continue
   last 30 days?
```

Permission is **revocable at any time**: setting `is_enabled = False` via the
API stops the agent on the next scheduled cycle with no further applications
submitted.

---

## 8. Data Inputs & Outputs

### Inputs to the Auto-Apply Engine

| Source | Field | Used For |
|---|---|---|
| `CustomUser` | `id`, `email`, `full_name` | User identification |
| `UserProfile` | `phone`, `target_role`, `location_preference` | Form-fill data (future) |
| `CVUpload` | `file` | CV attachment |
| `CVAnalysis` | `extracted_skills`, `raw_text` | Skill matching |
| `AutoApplySettings` | `is_enabled`, `min_match_score`, `max_applications_per_day`, `target_roles` | Gate & rule enforcement |
| `UserJobMatch` | `score`, `skill_overlap` | Job selection criteria |
| `JobListing` | `url`, `title`, `company`, `source` | Application target |

### Outputs

| Output | Type | Destination |
|---|---|---|
| `ApplicationLog` row | DB record | `auto_apply_ApplicationLog` table |
| In-app notification | DB record | `notifications_Notification` table |
| Email (optional) | Email | User's registered email |
| Celery task return | JSON | `{"status": "applied/failed/skipped", ...}` |

### Example API Response — `GET /api/auto-apply/settings/`

```json
{
  "is_enabled": true,
  "min_match_score": 0.60,
  "max_applications_per_day": 5,
  "target_roles": ["Python Developer", "Backend Engineer"]
}
```

### Example API Response — `GET /api/auto-apply/logs/`

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "job": {
      "id": "...",
      "title": "Python Developer",
      "company": "TechCorp",
      "location": "Lahore",
      "source": "rozee",
      "url": "https://www.rozee.pk/job/..."
    },
    "applied_at": "2026-04-08T07:30:00Z",
    "method": "auto",
    "status": "applied",
    "error_message": ""
  }
]
```

---

## 9. Celery Tasks & Scheduling

### Task Map

| Task Name | Module | Trigger | Description |
|---|---|---|---|
| `apps.jobs.tasks.scrape_rozee` | `jobs/tasks.py` | Scheduled / manual | Scrape Rozee.pk |
| `apps.jobs.tasks.scrape_indeed` | `jobs/tasks.py` | Scheduled / manual | Scrape Indeed |
| `apps.jobs.tasks.scrape_linkedin` | `jobs/tasks.py` | Scheduled / manual | Scrape LinkedIn |
| `apps.jobs.tasks.scrape_remotive` | `jobs/tasks.py` | Scheduled / manual | Scrape Remotive |
| `apps.jobs.tasks.scrape_weworkremotely` | `jobs/tasks.py` | Scheduled / manual | Scrape WeWorkRemotely |
| `apps.jobs.tasks.scrape_arbeitnow` | `jobs/tasks.py` | Scheduled / manual | Scrape Arbeitnow API |
| `apps.jobs.tasks.scrape_remoteok` | `jobs/tasks.py` | Scheduled / manual | Scrape RemoteOK API |
| `apps.jobs.tasks.scrape_all_sources` | `jobs/tasks.py` | Scheduled | Dispatch all scrapers |
| `apps.jobs.tasks.compute_matches_for_user` | `jobs/tasks.py` | Post-CV-upload / periodic | Semantic + keyword job matching |
| `apps.jobs.tasks.recompute_all_matches` | `jobs/tasks.py` | Scheduled | Recompute matches for all users |
| `apps.jobs.tasks.purge_expired_jobs` | `jobs/tasks.py` | Scheduled | Delete jobs older than 30 days |
| `auto_apply.run_auto_apply_for_all_users` | `auto_apply/tasks.py` | Scheduled | Dispatch per-user apply tasks |
| `auto_apply.run_auto_apply_for_user` | `auto_apply/tasks.py` | Per-user | Core apply logic |
| `notifications.create_notification` | `notifications/tasks.py` | Post-apply | In-app + email alert |

### Recommended Celery Beat Schedule

```python
# In Django admin → Periodic Tasks (django-celery-beat)
# Or in settings CELERY_BEAT_SCHEDULE:

CELERY_BEAT_SCHEDULE = {
    "scrape-all-jobs": {
        "task": "apps.jobs.tasks.scrape_all_sources",
        "schedule": crontab(hour="*/6"),          # every 6 hours
    },
    "recompute-all-matches": {
        "task": "apps.jobs.tasks.recompute_all_matches",
        "schedule": crontab(hour="*/4"),          # every 4 hours
    },
    "run-auto-apply": {
        "task": "auto_apply.run_auto_apply_for_all_users",
        "schedule": crontab(hour="*/2"),          # every 2 hours
    },
    "purge-expired-jobs": {
        "task": "apps.jobs.tasks.purge_expired_jobs",
        "schedule": crontab(hour=3, minute=0),    # daily at 03:00 UTC
    },
}
```

### Manual Trigger (CLI)

```bash
# Scrape a specific source
python manage.py scrape_jobs --source rozee

# Dry-run (no DB writes)
python manage.py scrape_jobs --source all --dry-run

# Trigger auto-apply via Celery task directly
celery -A career_platform call auto_apply.run_auto_apply_for_all_users
```

---

## 10. Logging & Monitoring

### Application-Level Logging

Every Celery task uses Python's standard `logging` module:

```python
logger = logging.getLogger(__name__)
logger.info("Auto-applied to %d jobs for user %s", applied_count, user_id)
logger.error("Auto-apply failed for job %s: %s", job.id, exc)
```

Configure log levels in `backend/career_platform/settings.py`:

```python
LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "apps.jobs": {"level": "DEBUG"},
        "apps.auto_apply": {"level": "DEBUG"},
    },
}
```

### Scraper Run Monitoring

Every scraper execution writes a `ScraperRun` record:

| Field | Meaning |
|---|---|
| `status` | `running` / `completed` / `failed` / `partial` |
| `jobs_found` | Total jobs fetched from source |
| `jobs_added` | New jobs written to DB |
| `jobs_updated` | Existing jobs refreshed |
| `jobs_skipped` | Duplicates skipped |
| `errors` | JSON list of error messages |
| `duration_seconds` | How long the run took |

View via: **GET** `/api/jobs/scraper-runs/` (admin only) or Django admin.

### Application Log Monitoring

`ApplicationLog` rows track every apply attempt:

- Filter by `status = "failed"` to diagnose errors.
- Filter by `applied_at__date = today` to see daily activity.
- Monitor `error_message` for patterns (CAPTCHA blocks, form errors, etc.).

---

## 11. Security & Privacy

### Authentication & Authorization

- All endpoints require a valid JWT access token (RS256 / HS256 via `simplejwt`).
- Refresh tokens are stored in httpOnly cookies, not localStorage.
- Role check (`IsStudent`) prevents employer/admin accounts from activating automation.

### CV Security

- CV files are stored in `MEDIA_ROOT/cvs/YYYY/MM/` with no public URL by default.
- Access is gated by Django views — raw file URLs are not served directly.
- Planned: encrypt CV files at rest (AES-256) using `django-encrypted-model-fields`
  or cloud storage KMS (AWS S3 SSE / GCS CMEK).

### Consent & Audit Trail

- `AutoApplySettings.is_enabled` stores explicit user consent.
- Every toggle (enable/disable) can be audited via API request logs.
- `ApplicationLog` is an **immutable** audit trail — no update/delete endpoints
  are exposed.
- Store the timestamp and version of terms accepted alongside `is_enabled`:
  consider adding `terms_version` and `consent_at` columns to
  `AutoApplySettings` for full compliance.

### Anti-Bot Protections (Job Board Side)

- `BaseScraper` uses `fake-useragent` to rotate User-Agent strings.
- Random delays (`time.sleep(random.uniform(...))`) between requests.
- If a source returns a CAPTCHA challenge, the scraper logs the error and stops
  that source (does **not** crash the worker).
- The auto-apply engine marks blocked jobs as `"blocked"` and does not retry
  automatically.

### Rate Limiting

- `max_applications_per_day` (default 5) limits the agent's daily output per user.
- Add Django REST Framework's `DEFAULT_THROTTLE_CLASSES` on the trigger endpoint
  to prevent abuse:

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"user": "10/minute"},
}
```

---

## 12. Frontend Integration (Website UI)

The UI for this module lives in:

```
frontend/src/pages/AutoApplyPage.tsx
```

### Current State

The page renders a placeholder. Full integration requires:

### Recommended UI Components

```
AutoApplyPage
├── ConsentBanner           ← Legal disclaimer + "I agree" checkbox
├── SettingsForm            ← is_enabled toggle, min_match_score slider,
│                              max_applications_per_day input, target_roles tags
├── TriggerButton           ← "Run Now" → POST /api/auto-apply/trigger/
└── ApplicationLogTable     ← GET /api/auto-apply/logs/
    ├── Columns: Job Title, Company, Applied At, Status, Error
    └── Status badges: applied (green), failed (red), skipped (grey)
```

### API Calls from React (using the shared Axios instance)

```typescript
// frontend/src/api/axios.ts base URL is '/api'

// 1. Fetch current settings
const res = await axios.get('/auto-apply/settings/');

// 2. Enable auto-apply with rules
await axios.patch('/auto-apply/settings/', {
  is_enabled: true,
  min_match_score: 0.65,
  max_applications_per_day: 5,
  target_roles: ['Python Developer', 'Backend Engineer'],
});

// 3. Manually trigger auto-apply
await axios.post('/auto-apply/trigger/');

// 4. Fetch application logs
const logs = await axios.get('/auto-apply/logs/');
```

> **Note:** Do **not** prefix paths with `/api/` — the Axios `baseURL` is
> already set to `/api` in `frontend/src/api/axios.ts`.

### Revoking Permission

```typescript
// Disable auto-apply
await axios.patch('/auto-apply/settings/', { is_enabled: false });
```

This immediately stops the agent on the next scheduled cycle.

---

## 13. Integration Steps (From Scratch)

Follow these steps to enable the module in a fresh environment:

### Step 1 — Environment Setup

```bash
# Clone repo and install dependencies
pip install -r backend/requirements.txt

# Copy and fill environment variables
cp backend/.env.example backend/.env
```

Required `.env` keys for this module:

```env
REDIS_URL=redis://localhost:6379/0
JOB_MATCH_SEMANTIC_WEIGHT=0.7
JOB_MATCH_KEYWORD_WEIGHT=0.3
JOB_MATCH_THRESHOLD=0.40
```

### Step 2 — Database Migrations

```bash
cd backend
python manage.py migrate
```

This creates tables for: `auto_apply_autoapplysettings`,
`auto_apply_applicationlog`, `jobs_joblisting`, `jobs_userjobmatch`,
`jobs_scraperrun`, etc.

### Step 3 — Start Services

```bash
# Terminal 1: Django API server
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Celery worker
celery -A career_platform worker --loglevel=info --concurrency=4

# Terminal 3: Celery Beat scheduler
celery -A career_platform beat --loglevel=info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Step 4 — Populate Job Data

```bash
# Scrape all sources (first run)
python manage.py scrape_jobs --source all

# Or trigger via Celery
celery -A career_platform call apps.jobs.tasks.scrape_all_sources
```

### Step 5 — Upload a CV

Use the frontend or POST to `/api/cv/upload/`. This triggers
`compute_matches_for_user` automatically via the CV upload signal.

### Step 6 — Enable Auto-Apply via UI or API

```http
PATCH /api/auto-apply/settings/
Authorization: Bearer <token>
Content-Type: application/json

{
  "is_enabled": true,
  "min_match_score": 0.60,
  "max_applications_per_day": 5,
  "target_roles": ["Python Developer"]
}
```

### Step 7 — Verify Logs

```http
GET /api/auto-apply/logs/
Authorization: Bearer <token>
```

---

## 14. Error Handling & Retry Logic

| Scenario | Behavior |
|---|---|
| Scraper HTTP failure | Log error in `ScraperRun.errors`; continue to next page/source |
| JSON parse error | Log error; skip that page |
| Job already exists (duplicate URL) | Increment `jobs_skipped` counter; no duplicate row |
| Celery task exception | Auto-retry up to 3 times with exponential backoff |
| User not found in auto-apply task | Task exits cleanly (no retry) |
| Auto-apply settings missing | Task exits cleanly (no retry) |
| Daily quota exhausted | Task logs info and exits cleanly |
| Application already submitted (30-day window) | Logged as `skipped`; loop continues |
| Application form error (future Playwright layer) | Logged as `failed` with `error_message`; retry once |
| CAPTCHA / anti-bot block | Logged as `blocked`; no retry |
| Unknown form field required | Logged as `failed`; request user input via notification |

---

## 15. Extending the Module

### Adding a New Job Source Scraper

1. Create `backend/apps/jobs/scrapers/<source>_scraper.py`.
2. Subclass `BaseScraper` and implement `fetch_jobs() -> int`.
3. Register in `backend/apps/jobs/scrapers/__init__.py`.
4. Add a Celery task in `backend/apps/jobs/tasks.py` following the existing pattern.
5. Add the new source to `JobListing.Source` and `ScraperRun.SourceChoice` choices.
6. Run `python manage.py makemigrations jobs && python manage.py migrate`.

### Adding Real Form-Fill Automation (Playwright)

The current `run_auto_apply_for_user` task logs the application but does **not**
actually fill a job application form. To add real automation:

1. Install Playwright: `pip install playwright && playwright install chromium`.
2. In `auto_apply/tasks.py`, replace the `# Log application` block with:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(job.url)
    # Fill fields using user profile data
    page.fill('#name', user.full_name)
    page.fill('#email', user.email)
    page.set_input_files('#cv-upload', cv_file_path)
    page.click('#submit-button')
    browser.close()
```

3. Handle `CAPTCHA` exceptions and mark the log as `"blocked"`.

### Adding a `target_roles` Filter

The `target_roles` JSON field on `AutoApplySettings` is stored but currently not
applied as a hard filter in the task. To activate it:

```python
# In run_auto_apply_for_user, after loading matches:
if settings_obj.target_roles:
    roles_lower = [r.lower() for r in settings_obj.target_roles]
    matches = [
        m for m in matches
        if any(role in m.job.title.lower() for role in roles_lower)
    ]
```

---

*This document reflects the codebase as of April 2026. Keep it updated alongside
code changes to `apps/auto_apply/`, `apps/jobs/`, and `frontend/src/pages/AutoApplyPage.tsx`.*
