@echo off
echo ========================================
echo   Dermavision Backend Server
echo ========================================
echo.

REM Activate virtual environment
echo [1/2] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [2/2] Starting server...
echo.
echo Server will be available at:
echo   - Swagger UI: http://localhost:8000/docs
echo   - Health: http://localhost:8000/api/v1/health
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
