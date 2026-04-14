#!/usr/bin/env bash
# One-click launcher for WSL2 (Ubuntu).
# Run from the repository root:
#   cd /mnt/d/AI-Career-Assistant
#   bash start-local.sh
#
# Assumes a shared virtualenv at backend/.venv (created in README step 3).
# All services are started in the background; logs go to /tmp/ai-career-*.log.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT_DIR/backend/.venv"
ACTIVATE="$VENV/bin/activate"

# ── Preflight check ────────────────────────────────────────────────────────────
if [ ! -f "$ACTIVATE" ]; then
  echo "[ERROR] Python virtual environment not found at: $VENV"
  echo ""
  echo "Create it first from the repository root:"
  echo "  1) cd $ROOT_DIR"
  echo "  2) python3.11 -m venv backend/.venv"
  echo "  3) source backend/.venv/bin/activate"
  echo "  4) pip install -r backend/requirements.txt"
  echo "  5) pip install -r fastapi_service/requirements.txt"
  exit 1
fi

# ── Helper: run a command in the background, writing to a log file ─────────────
start_service() {
  local name="$1"
  local logfile="/tmp/ai-career-${name// /-}.log"
  shift
  echo "  Starting $name → $logfile"
  # shellcheck disable=SC1090
  (source "$ACTIVATE" && "$@") >"$logfile" 2>&1 &
  echo $! > "/tmp/ai-career-${name// /-}.pid"
}

echo "Starting all services..."
echo ""

# Terminal 1 — Django (runs migrate first)
(
  source "$ACTIVATE"
  cd "$ROOT_DIR/backend"
  python manage.py migrate --run-syncdb
  python manage.py runserver 0.0.0.0:8000
) > /tmp/ai-career-django.log 2>&1 &
echo $! > /tmp/ai-career-django.pid
echo "  Starting Django (port 8000) → /tmp/ai-career-django.log"

# Terminal 2 — Celery Worker
(
  source "$ACTIVATE"
  cd "$ROOT_DIR/backend"
  exec celery -A career_platform worker --loglevel=info --concurrency=4
) > /tmp/ai-career-celery-worker.log 2>&1 &
echo $! > /tmp/ai-career-celery-worker.pid
echo "  Starting Celery Worker → /tmp/ai-career-celery-worker.log"

# Terminal 3 — Celery Beat
(
  source "$ACTIVATE"
  cd "$ROOT_DIR/backend"
  exec celery -A career_platform beat --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
) > /tmp/ai-career-celery-beat.log 2>&1 &
echo $! > /tmp/ai-career-celery-beat.pid
echo "  Starting Celery Beat → /tmp/ai-career-celery-beat.log"

# Terminal 4 — FastAPI AI service
(
  source "$ACTIVATE"
  cd "$ROOT_DIR/fastapi_service"
  exec uvicorn main:app --host 0.0.0.0 --port 8001 --reload
) > /tmp/ai-career-fastapi.log 2>&1 &
echo $! > /tmp/ai-career-fastapi.pid
echo "  Starting FastAPI (port 8001) → /tmp/ai-career-fastapi.log"

# Terminal 5 — React dev server
(
  cd "$ROOT_DIR/frontend"
  exec npm run dev -- --host 0.0.0.0 --port 5173
) > /tmp/ai-career-react.log 2>&1 &
echo $! > /tmp/ai-career-react.pid
echo "  Starting React (port 5173) → /tmp/ai-career-react.log"

echo ""
echo "All services running in the background."
echo ""
echo "  Frontend:      http://localhost:5173"
echo "  Django API:    http://localhost:8000/api/"
echo "  Django admin:  http://localhost:8000/admin/"
echo "  FastAPI:       http://localhost:8001"
echo "  FastAPI docs:  http://localhost:8001/docs"
echo ""
echo "To stream combined logs:"
echo "  tail -f /tmp/ai-career-*.log"
echo ""
echo "To stop all services:"
echo "  kill \$(cat /tmp/ai-career-*.pid) 2>/dev/null; rm -f /tmp/ai-career-*.pid"
echo ""

# Tail combined logs so the terminal stays useful
tail -f /tmp/ai-career-django.log \
        /tmp/ai-career-celery-worker.log \
        /tmp/ai-career-celery-beat.log \
        /tmp/ai-career-fastapi.log \
        /tmp/ai-career-react.log
