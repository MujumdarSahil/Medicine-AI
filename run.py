"""
MedMentor AI — Unified Launcher
Run this file to start the entire system.
It automatically checks if the database is empty and ingests the PDF on the first run.

Usage: python run.py
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

# Detect venv python
if sys.platform == "win32":
    root_venv = ROOT / "venv" / "Scripts" / "python.exe"
    back_venv = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    if root_venv.exists():
        VENV_PYTHON = root_venv
        VENV_UVICORN = ROOT / "venv" / "Scripts" / "uvicorn.exe"
    else:
        VENV_PYTHON = back_venv
        VENV_UVICORN = BACKEND_DIR / "venv" / "Scripts" / "uvicorn.exe"
else:
    root_venv = ROOT / "venv" / "bin" / "python"
    back_venv = BACKEND_DIR / "venv" / "bin" / "python"
    if root_venv.exists():
        VENV_PYTHON = root_venv
        VENV_UVICORN = ROOT / "venv" / "bin" / "uvicorn"
    else:
        VENV_PYTHON = back_venv
        VENV_UVICORN = BACKEND_DIR / "venv" / "bin" / "uvicorn"

PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
UVICORN = str(VENV_UVICORN) if VENV_UVICORN.exists() else "uvicorn"

# ANSI colours
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

processes: list[subprocess.Popen] = []


def prefix_stream(proc: subprocess.Popen, label: str, color: str):
    """Read a process stream line-by-line and print with a coloured prefix."""
    prefix = f"{color}{BOLD}[{label}]{RESET} "
    try:
        for line in iter(proc.stdout.readline, b""):
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                print(prefix + text)
    except Exception:
        pass


def check_db_status() -> str:
    """
    Check database status.
    Returns:
      "empty": MongoDB is running but has 0 chapters
      "populated": MongoDB is running and has chapters
      "offline": MongoDB is not running or connection failed
      "unknown": Unknown status (e.g. venv not ready)
    """
    if not VENV_PYTHON.exists():
        return "unknown"
    
    code = (
        "import asyncio\n"
        "from motor.motor_asyncio import AsyncIOMotorClient\n"
        "async def check():\n"
        "    try:\n"
        "        client = AsyncIOMotorClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)\n"
        "        db = client['jarvis']\n"
        "        count = await db['med_chapters'].count_documents({})\n"
        "        print(count)\n"
        "        client.close()\n"
        "    except Exception:\n"
        "        print(-1)\n"
        "asyncio.run(check())\n"
    )
    try:
        res = subprocess.run(
            [PYTHON, "-c", code],
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            output = res.stdout.strip()
            if output == "-1":
                return "offline"
            elif output.isdigit():
                count = int(output)
                return "empty" if count == 0 else "populated"
    except Exception:
        pass
    return "unknown"


def run_ingestion():
    """Run the PDF ingestion script and block until completion."""
    print(f"\n{YELLOW}{BOLD}[DATABASE]{RESET} Checking PDF path configuration...")
    
    # Read MEDICINE_PDF_PATH from backend/.env
    env_file = BACKEND_DIR / ".env"
    pdf_path = ""
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("MEDICINE_PDF_PATH="):
                pdf_path = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
                
    if not pdf_path or not Path(pdf_path).exists():
        print(f"\n{RED}{BOLD}[ERROR]{RESET} PDF not found at: '{pdf_path}'")
        print("        Please ensure MEDICINE_PDF_PATH is correctly configured in backend/.env")
        print("        App startup aborted.")
        sys.exit(1)
        
    print(f"{GREEN}✓ PDF found at: '{pdf_path}'{RESET}")
    print(f"{YELLOW}{BOLD}[DATABASE]{RESET} Database is empty. Running PDF ingestion automatically (this may take a few minutes)...")
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    # Force UTF-8 encoding for Python outputs to prevent Windows encoding crashes
    env["PYTHONIOENCODING"] = "utf-8"
    
    proc = subprocess.Popen(
        [PYTHON, "ingest_pdf.py"],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env
    )
    
    # Stream the output so the user sees progress
    prefix_stream(proc, "INGEST", YELLOW)
    proc.wait()
    
    if proc.returncode == 0:
        print(f"\n{GREEN}{BOLD}[DATABASE]{RESET} PDF ingestion completed successfully.{RESET}")
    else:
        print(f"\n{RED}{BOLD}[ERROR]{RESET} PDF ingestion failed with code {proc.returncode}. Please check your configuration.{RESET}")
        sys.exit(1)


def start_backend() -> subprocess.Popen:
    print(f"\n{GREEN}{BOLD}[BACKEND]{RESET} Starting FastAPI on http://localhost:8000 ...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.Popen(
        [UVICORN, "app.main:app", "--reload", "--port", "8000", "--host", "0.0.0.0"],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    thread = threading.Thread(target=prefix_stream, args=(proc, "BACKEND", GREEN), daemon=True)
    thread.start()
    return proc


def start_frontend() -> subprocess.Popen:
    print(f"\n{CYAN}{BOLD}[FRONTEND]{RESET} Starting Vue/Vite dev server on http://localhost:5173 ...")

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    thread = threading.Thread(target=prefix_stream, args=(proc, "FRONTEND", CYAN), daemon=True)
    thread.start()
    return proc


def check_prerequisites():
    issues = []

    # Check venv
    if not VENV_PYTHON.exists():
        issues.append(
            f"{YELLOW}  ⚠  No Python venv found at venv/ or backend/venv.\n"
            f"     Run: python -m venv venv && venv\\Scripts\\activate && pip install -r backend\\requirements.txt{RESET}"
        )

    # Check node_modules
    if not (FRONTEND_DIR / "node_modules").exists():
        issues.append(
            f"{YELLOW}  ⚠  No node_modules found in frontend/.\n"
            f"     Run: cd frontend && npm install{RESET}"
        )

    # Check .env
    env_file = BACKEND_DIR / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        if "your_groq_api_key_here" in content:
            issues.append(
                f"{YELLOW}  ⚠  backend/.env still has placeholder API keys.\n"
                f"     Edit backend/.env and set GROQ_API_KEY / GEMINI_API_KEY.{RESET}"
            )

    return issues


def shutdown(signum=None, frame=None):
    print(f"\n\n{BOLD}Shutting down MedMentor AI...{RESET}")
    for proc in processes:
        try:
            proc.terminate()
        except Exception:
            pass
    # Wait briefly then force-kill
    time.sleep(1)
    for proc in processes:
        try:
            proc.kill()
        except Exception:
            pass
    print(f"{GREEN}✓ All processes stopped.{RESET}\n")
    sys.exit(0)


def main():
    # Force output encoding of stdout to UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print(f"""
{BOLD}{CYAN}
  +------------------------------------------+
  |        🩺  MedMentor AI Launcher         |
  |   MBBS Medicine AI Tutor — Full Stack    |
  +------------------------------------------+
{RESET}""")

    # Prerequisite checks
    issues = check_prerequisites()
    if issues:
        print(f"{BOLD}Pre-flight checks:{RESET}")
        for issue in issues:
            print(issue)
        print()
        sys.exit(1)

    # Database Check and Auto-Ingestion
    db_status = check_db_status()
    if db_status == "offline":
        print(f"{RED}{BOLD}[ERROR]{RESET} MongoDB is offline or could not be reached.")
        print("        Please ensure MongoDB is running on mongodb://localhost:27017 before starting the app.")
        sys.exit(1)
    elif db_status == "empty":
        run_ingestion()
    elif db_status == "populated":
        print(f"{GREEN}{BOLD}[DATABASE]{RESET} Database is already populated. Skipping ingestion.{RESET}")
    else:
        print(f"{YELLOW}{BOLD}[DATABASE]{RESET} Database status unknown. Proceeding to boot.{RESET}")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start services
    backend_proc = start_backend()
    processes.append(backend_proc)

    time.sleep(2)  # Give backend a moment to bind

    frontend_proc = start_frontend()
    processes.append(frontend_proc)

    print(f"""
{BOLD}
  +----------------------------------------+
  |  ✅  MedMentor AI is running!          |
  |                                        |
  |  🌐  App       : http://localhost:5173 |
  |  📡  API       : http://localhost:8000 |
  |  📄  API Docs  : http://localhost:8000/docs |
  |                                        |
  |  Press  Ctrl+C  to stop all servers   |
  +----------------------------------------+
{RESET}""")

    # Monitor processes — restart if either dies unexpectedly
    try:
        while True:
            time.sleep(3)
            if backend_proc.poll() is not None:
                print(f"\n{RED}[BACKEND] Process exited (code {backend_proc.returncode}). Restarting...{RESET}")
                processes.remove(backend_proc)
                backend_proc = start_backend()
                processes.append(backend_proc)

            if frontend_proc.poll() is not None:
                print(f"\n{RED}[FRONTEND] Process exited (code {frontend_proc.returncode}). Restarting...{RESET}")
                processes.remove(frontend_proc)
                frontend_proc = start_frontend()
                processes.append(frontend_proc)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
