@echo off
setlocal

REM One-click launcher for D:\AI-Career-Assistant (Windows native).
REM Assumes a shared virtualenv at backend\.venv (created in README step 3).
REM Celery uses --pool=solo because Windows does not support the default prefork pool.

set ROOT_DIR=%~dp0
set VENV_ACTIVATE=%ROOT_DIR%backend\.venv\Scripts\activate.bat

if not exist "%VENV_ACTIVATE%" (
  echo [ERROR] Python virtual environment not found at:
  echo         %VENV_ACTIVATE%
  echo.
  echo Create it first from the repository root:
  echo   1^) cd /d %ROOT_DIR%
  echo   2^) python -m venv backend\.venv
  echo   3^) backend\.venv\Scripts\activate
  echo   4^) pip install -r backend\requirements.txt
  echo   5^) pip install -r fastapi_service\requirements.txt
  echo.
  pause
  exit /b 1
)

echo Starting all services...
echo.

start "Django (port 8000)" cmd /k "cd /d %ROOT_DIR%backend && call \"%VENV_ACTIVATE%\" && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"
start "Celery Worker" cmd /k "cd /d %ROOT_DIR%backend && call \"%VENV_ACTIVATE%\" && celery -A career_platform worker --loglevel=info --pool=solo"
start "Celery Beat" cmd /k "cd /d %ROOT_DIR%backend && call \"%VENV_ACTIVATE%\" && celery -A career_platform beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
start "FastAPI (port 8001)" cmd /k "cd /d %ROOT_DIR%fastapi_service && call \"%VENV_ACTIVATE%\" && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
start "React (port 5173)" cmd /k "cd /d %ROOT_DIR%frontend && npm run dev -- --host 0.0.0.0 --port 5173"

echo All services launched in separate windows.
echo.
echo   Frontend:      http://localhost:5173
echo   Django API:    http://localhost:8000/api/
echo   Django admin:  http://localhost:8000/admin/
echo   FastAPI:       http://localhost:8001
echo   FastAPI docs:  http://localhost:8001/docs
echo.
echo Close the individual service windows to stop each service.

endlocal

