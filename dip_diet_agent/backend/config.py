"""
Configuration and environment variable management for DIP Diet RAG Agent.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"

# On Render (and other read-only filesystems) write mutable data to /tmp.
# Render sets the "RENDER" environment variable automatically on all services.
_ON_RENDER = bool(os.getenv("RENDER"))
_WRITABLE_ROOT = Path("/tmp/dip_diet") if _ON_RENDER else DATA_DIR

PROFILES_DIR = _WRITABLE_ROOT / "profiles"
CHROMA_DB_DIR = _WRITABLE_ROOT / "chroma_db"

# Ensure directories exist
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# ── IBM WatsonX Configuration ─────────────────────────────────────────────────
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

# IBM Granite Model ID
GRANITE_MODEL_ID = os.getenv(
    "GRANITE_MODEL_ID",
    "ibm/granite-13b-instruct-v2"
)

# ── Embedding Configuration ───────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
)

# ── RAG Configuration ─────────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "4"))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "dip_diet_kb")

# ── LLM Generation Parameters ────────────────────────────────────────────────
LLM_MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", "800"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.95"))
LLM_REPETITION_PENALTY = float(os.getenv("LLM_REPETITION_PENALTY", "1.1"))

# ── Server Configuration ──────────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ── CORS ──────────────────────────────────────────────────────────────────────
# Comma-separated list of allowed origins.
# Default "*" works for same-origin serving; set explicitly for cross-origin.
ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS: list = (
    ["*"]
    if ALLOWED_ORIGINS_RAW.strip() == "*"
    else [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
)

# ── Safety Guardrails ─────────────────────────────────────────────────────────
MEDICAL_DISCLAIMER = (
    "⚕️ MEDICAL DISCLAIMER: This information is for educational purposes only "
    "and is NOT a substitute for professional medical advice. Please consult a "
    "qualified healthcare provider or registered dietitian before making "
    "significant dietary changes, especially if you have a medical condition."
)

SAFETY_KEYWORDS = [
    "diagnose", "diagnosis", "prescription", "prescribe", "medication",
    "drug", "disease", "cure", "treat", "surgery", "overdose", "poison",
    "suicide", "self-harm", "anorexia", "bulimia", "eating disorder"
]

SAFETY_RESPONSE = (
    "I'm here to provide general nutrition guidance based on the DIP Diet framework. "
    "For medical diagnoses, prescriptions, or treatment of health conditions, "
    "please consult a qualified healthcare professional. "
    + MEDICAL_DISCLAIMER
)

# ── Demo / Fallback Mode ──────────────────────────────────────────────────────
# When True, uses a rule-based fallback if WatsonX credentials are not set.
DEMO_MODE = not bool(WATSONX_API_KEY and WATSONX_PROJECT_ID)
