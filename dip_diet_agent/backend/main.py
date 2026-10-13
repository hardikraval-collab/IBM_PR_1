"""
DIP Diet RAG Agent — FastAPI Application
Main entry point for the web server.
"""
import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import PROFILES_DIR, MEDICAL_DISCLAIMER, DEMO_MODE, ALLOWED_ORIGINS
from backend.models import (
    UserProfile,
    ChatRequest,
    ChatResponse,
    MealPlanRequest,
    MealPlanResponse,
    ShoppingListResponse,
    SubstitutionRequest,
    SubstitutionResponse,
    IngestRequest,
    DayPlan,
    Meal,
    ShoppingItem,
    SourceCitation,
)
from backend.rag_pipeline import rag_pipeline
from backend.ingest import ingest_all_knowledge_base_docs
from backend.meal_plan_generator import generate_structured_meal_plan
from backend.shopping_list_generator import generate_shopping_list

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — runs on startup and shutdown."""
    # Startup
    logger.info("DIP Diet RAG Agent starting up...")
    logger.info(f"Mode: {'DEMO (no WatsonX)' if DEMO_MODE else 'PRODUCTION (IBM Granite)'}")
    count = ingest_all_knowledge_base_docs()
    logger.info(f"Knowledge base ready. Total chunks: {count + rag_pipeline.collection.count()}")
    yield
    # Shutdown
    logger.info("DIP Diet RAG Agent shutting down.")


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="DIP Diet RAG Agent",
    description=(
        "Personalized nutrition assistant powered by IBM Granite LLM and RAG. "
        "Provides DIP Diet meal plans, nutrition Q&A, and food substitutions."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Static Files (Frontend) ───────────────────────────────────────────────────
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    """Serve the frontend SPA."""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "DIP Diet RAG Agent API is running!", "docs": "/api/docs"}


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mode": "demo" if DEMO_MODE else "production",
        "knowledge_base_chunks": rag_pipeline.collection.count(),
        "llm_model": "IBM Granite (WatsonX)" if not DEMO_MODE else "Demo Mode",
        "disclaimer": MEDICAL_DISCLAIMER,
    }


# ── User Profile ──────────────────────────────────────────────────────────────
@app.post("/api/profile", response_model=dict)
async def save_profile(profile: UserProfile):
    """Save or update a user profile."""
    if not profile.user_id:
        profile.user_id = f"user_{str(uuid.uuid4())[:8]}"

    profile_path = Path(PROFILES_DIR) / f"{profile.user_id}.json"
    profile_data = profile.model_dump()
    profile_path.write_text(json.dumps(profile_data, indent=2), encoding="utf-8")

    logger.info(f"Profile saved for user: {profile.user_id}")
    return {
        "success": True,
        "user_id": profile.user_id,
        "message": f"Profile saved successfully for {profile.name}!",
    }


@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Retrieve a user profile by ID."""
    profile_path = Path(PROFILES_DIR) / f"{user_id}.json"
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail=f"Profile not found for user: {user_id}")
    return json.loads(profile_path.read_text(encoding="utf-8"))


# ── Chat / RAG Q&A ────────────────────────────────────────────────────────────
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Conversational RAG endpoint.
    Retrieves relevant nutrition docs and generates a personalised response.
    """
    # Load user profile for personalisation
    user_profile = None
    profile_path = Path(PROFILES_DIR) / f"{request.user_id}.json"
    if profile_path.exists():
        user_profile = json.loads(profile_path.read_text(encoding="utf-8"))

    history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.conversation_history
    ]

    response_text, sources, is_safe = rag_pipeline.generate_rag_response(
        query=request.message,
        user_profile=user_profile,
        conversation_history=history,
    )

    return ChatResponse(
        response=response_text,
        sources=sources,
        disclaimer=MEDICAL_DISCLAIMER,
        is_safe=is_safe,
    )


# ── Meal Plan ─────────────────────────────────────────────────────────────────
@app.post("/api/meal-plan", response_model=MealPlanResponse)
async def get_meal_plan(request: MealPlanRequest):
    """Generate a personalized daily or weekly meal plan."""
    profile_path = Path(PROFILES_DIR) / f"{request.user_id}.json"
    if not profile_path.exists():
        raise HTTPException(
            status_code=404,
            detail="User profile not found. Please create your profile first.",
        )

    user_profile = json.loads(profile_path.read_text(encoding="utf-8"))
    meal_plan = generate_structured_meal_plan(user_profile, request.plan_type)
    return meal_plan


# ── Shopping List ─────────────────────────────────────────────────────────────
@app.post("/api/shopping", response_model=ShoppingListResponse)
async def get_shopping_list(request: MealPlanRequest):
    """Generate a shopping list based on the user's meal plan."""
    profile_path = Path(PROFILES_DIR) / f"{request.user_id}.json"
    if not profile_path.exists():
        raise HTTPException(
            status_code=404,
            detail="User profile not found. Please create your profile first.",
        )

    user_profile = json.loads(profile_path.read_text(encoding="utf-8"))
    shopping = generate_shopping_list(user_profile)
    return shopping


# ── Food Substitution ─────────────────────────────────────────────────────────
@app.post("/api/substitute", response_model=SubstitutionResponse)
async def get_substitution(request: SubstitutionRequest):
    """Get healthy food substitutions for a given ingredient."""
    user_profile = None
    profile_path = Path(PROFILES_DIR) / f"{request.user_id}.json"
    if profile_path.exists():
        user_profile = json.loads(profile_path.read_text(encoding="utf-8"))

    from backend.llm_client import llm_client
    prompt = rag_pipeline.generate_substitution_prompt(
        food_item=request.food_item,
        reason=request.reason or "",
        user_profile=user_profile or {},
    )
    response_text = llm_client.generate(prompt)

    return SubstitutionResponse(
        original_food=request.food_item,
        substitutions=[
            {"name": "See response", "notes": "Parsed from LLM output"},
        ],
        explanation=response_text,
        disclaimer=MEDICAL_DISCLAIMER,
    )


# ── Document Ingestion ────────────────────────────────────────────────────────
@app.post("/api/ingest")
async def ingest_document(request: IngestRequest):
    """Ingest a nutrition document into the knowledge base."""
    n_chunks = rag_pipeline.ingest_text(
        content=request.content,
        title=request.title,
        source_name=request.source_name,
    )
    return {
        "success": True,
        "chunks_ingested": n_chunks,
        "total_chunks": rag_pipeline.collection.count(),
        "message": f"Successfully ingested '{request.title}' ({n_chunks} chunks)",
    }


@app.post("/api/ingest/file")
async def ingest_file_upload(file: UploadFile = File(...)):
    """Upload and ingest a nutrition document file."""
    if not file.filename.endswith((".txt", ".md", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Only .txt, .md, and .csv files are supported.",
        )
    content = (await file.read()).decode("utf-8")
    n_chunks = rag_pipeline.ingest_text(
        content=content,
        title=file.filename.replace("_", " ").replace(".txt", "").replace(".md", ""),
        source_name=file.filename,
    )
    return {
        "success": True,
        "filename": file.filename,
        "chunks_ingested": n_chunks,
        "total_chunks": rag_pipeline.collection.count(),
    }


# ── Nutrition Dashboard ───────────────────────────────────────────────────────
@app.get("/api/dashboard/{user_id}")
async def get_dashboard(user_id: str):
    """Get nutrition dashboard data for a user."""
    profile_path = Path(PROFILES_DIR) / f"{user_id}.json"
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="User profile not found.")

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    from backend.meal_plan_generator import calculate_tdee, get_macro_targets

    tdee = calculate_tdee(profile)
    macros = get_macro_targets(profile, tdee)

    return {
        "user_name": profile.get("name", "User"),
        "tdee_kcal": tdee,
        "macros": macros,
        "bmi": _calculate_bmi(profile),
        "diet_preference": profile.get("diet_preference"),
        "activity_level": profile.get("activity_level"),
        "goals": profile.get("nutrition_goals", []),
        "disclaimer": MEDICAL_DISCLAIMER,
    }


def _calculate_bmi(profile: dict) -> Optional[float]:
    """Calculate BMI if height and weight are available."""
    weight = profile.get("weight_kg")
    height = profile.get("height_cm")
    if weight and height and height > 0:
        bmi = weight / ((height / 100) ** 2)
        return round(bmi, 1)
    return None


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    from backend.config import HOST, PORT, DEBUG

    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info",
    )
