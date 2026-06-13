@echo off
echo ========================================
echo   MedMentor AI -- Backend Startup
echo ========================================
cd /d "%~dp0backend"
echo [1] Activating virtual environment...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [!] No venv found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)
echo [2] Starting FastAPI server on port 8000...
uvicorn app.main:app --reload --port 8000
