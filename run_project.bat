@echo off
REM ═══════════════════════════════════════════════════════════════════════
REM  DIP Diet RAG Agent — Windows Startup Script
REM  Powered by IBM Granite LLM, IBM Cloud, and IBM Bob
REM ═══════════════════════════════════════════════════════════════════════
title DIP Diet RAG Agent

echo.
echo  ██████╗ ██╗██████╗     ██████╗ ██╗███████╗████████╗
echo  ██╔══██╗██║██╔══██╗    ██╔══██╗██║██╔════╝╚══██╔══╝
echo  ██║  ██║██║██████╔╝    ██║  ██║██║█████╗     ██║
echo  ██║  ██║██║██╔═══╝     ██║  ██║██║██╔══╝     ██║
echo  ██████╔╝██║██║         ██████╔╝██║███████╗   ██║
echo  ╚═════╝ ╚═╝╚═╝         ╚═════╝ ╚═╝╚══════╝   ╚═╝
echo.
echo  Powered by IBM Granite LLM  ^|  IBM Cloud  ^|  IBM Bob
echo  ══════════════════════════════════════════════════════
echo.

REM ── Check Python ───────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [OK] Python found.

REM ── Navigate to agent directory ────────────────────────────────────────────
cd /d "%~dp0dip_diet_agent"
if errorlevel 1 (
    echo [ERROR] Could not find dip_diet_agent directory.
    pause
    exit /b 1
)

REM ── Create virtual environment if not exists ───────────────────────────────
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)

REM ── Activate virtual environment ───────────────────────────────────────────
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM ── Install / upgrade dependencies ────────────────────────────────────────
echo [INFO] Installing dependencies (this may take a few minutes on first run)...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARN] Some packages may have had issues. Trying core packages individually...
    pip install fastapi "uvicorn[standard]" python-multipart pydantic python-dotenv --quiet
    pip install sentence-transformers chromadb langchain langchain-text-splitters --quiet
    pip install ibm-watsonx-ai --quiet
)
echo [OK] Dependencies installed.

REM ── Setup .env file ────────────────────────────────────────────────────────
if not exist ".env" (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env >nul 2>&1
    echo.
    echo [NOTICE] .env file created. The agent will run in DEMO MODE.
    echo          To use IBM Granite LLM, edit dip_diet_agent\.env and set:
    echo            WATSONX_API_KEY=your_api_key
    echo            WATSONX_PROJECT_ID=your_project_id
    echo.
)

REM ── Ensure data directories exist ─────────────────────────────────────────
if not exist "data\profiles" mkdir "data\profiles"
if not exist "data\knowledge_base" mkdir "data\knowledge_base"
if not exist "data\chroma_db" mkdir "data\chroma_db"

echo.
echo  ┌────────────────────────────────────────────────────────────────┐
echo  │  DIP Diet Agent is starting...                                 │
echo  │                                                                │
echo  │  NOTE: First startup downloads the AI embedding model         │
echo  │        (~80 MB). This can take 60-120 seconds.                │
echo  │        Please wait for the "Application startup complete"      │
echo  │        message before opening the browser.                     │
echo  │                                                                │
echo  │  App:  http://localhost:8000                                   │
echo  │  Docs: http://localhost:8000/api/docs                          │
echo  │                                                                │
echo  │  Press Ctrl+C to stop the server                               │
echo  └────────────────────────────────────────────────────────────────┘
echo.

REM ── Wait for "Application startup complete" then open browser ─────────────
REM    Polls port 8000 every 5 seconds for up to 3 minutes, then opens browser.
start "" cmd /c "^
for /L %%i in (1,1,36) do (^
    timeout /t 5 >nul 2>&1 ^&^& ^
    powershell -Command \"try { $r = Invoke-WebRequest http://localhost:8000/api/health -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; if ($r.StatusCode -eq 200) { start http://localhost:8000; exit 0 } } catch {}\" ^
) ^
"

REM ── Start the FastAPI server (no --reload so it starts faster) ────────────
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

REM ── If server exits ────────────────────────────────────────────────────────
echo.
echo [INFO] Server stopped.
pause
