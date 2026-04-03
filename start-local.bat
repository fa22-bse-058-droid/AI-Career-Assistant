@echo off
setlocal

REM Assumes a single shared virtualenv at backend\.venv (as documented in README).
REM If you use a different location, update VENV_ACTIVATE below.

set ROOT_DIR=%~dp0
set VENV_ACTIVATE=%ROOT_DIR%backend\.venv\Scripts\activate.bat

if not exist "%VENV_ACTIVATE%" (
  echo [ERROR] Python virtual environment not found at:
  echo         %VENV_ACTIVATE%
  echo Create it first from repository root:
  echo   cd /d %ROOT_DIR%^&^& python -m venv backend\.venv
  exit /b 1
)

echo Starting services...

start "Django" cmd /k "cd /d %ROOT_DIR%backend && call \"%VENV_ACTIVATE%\" && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"
start "Celery Worker" cmd /k "cd /d %ROOT_DIR%backend && call \"%VENV_ACTIVATE%\" && celery -A career_platform worker --loglevel=info --concurrency=4"
start "Celery Beat" cmd /k "cd /d %ROOT_DIR%backend && call \"%VENV_ACTIVATE%\" && celery -A career_platform beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
start "FastAPI" cmd /k "cd /d %ROOT_DIR%fastapi_service && call \"%VENV_ACTIVATE%\" && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
start "React" cmd /k "cd /d %ROOT_DIR%frontend && npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo All startup commands launched in separate windows.
echo Frontend: http://localhost:5173
echo Django API: http://localhost:8000/api/
echo FastAPI: http://localhost:8001

endlocal
