# DIP Diet RAG Agent

> **Personalized nutrition assistant powered by IBM Granite LLM, IBM WatsonX.ai, and IBM Bob.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![IBM Granite](https://img.shields.io/badge/IBM-Granite%20LLM-1a56db)](https://www.ibm.com/products/watsonx-ai)
[![ChromaDB](https://img.shields.io/badge/Vector%20DB-ChromaDB-orange)](https://trychroma.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ⚕️ Medical Disclaimer

> This application provides general nutrition information for **educational purposes only**.  
> It is **NOT** a substitute for professional medical advice, diagnosis, or treatment.  
> Always consult a qualified healthcare provider or registered dietitian before making significant dietary changes.

---

## 🎯 Objectives

The DIP Diet RAG Agent aims to:

- Deliver **personalized, evidence-based nutrition guidance** using the DIP (Discipline Intermittent Protocol) Diet framework.
- Leverage **Retrieval-Augmented Generation (RAG)** with IBM Granite LLM to answer nutrition questions grounded in a curated knowledge base.
- Generate **tailored meal plans and shopping lists** based on user dietary preferences, allergies, medical history, and goals.
- Provide a **safe, ethical AI experience** with safety guardrails, medical disclaimers, and culturally inclusive recommendations.

---

## 🚀 Quick Start (Windows)

```bash
# From the repository root:
run_project.bat
```

Then open your browser at **http://localhost:8000**  
API documentation: **http://localhost:8000/api/docs**

---

## 🥗 Features

| Feature | Description |
|---------|-------------|
| 👤 **User Profile** | Personalized setup: age, diet, allergies, medical history, goals, location |
| 💬 **RAG Q&A Chat** | Nutrition questions answered using retrieved documents + IBM Granite LLM |
| 📅 **Meal Plans** | Daily and weekly plans tailored to the user's profile |
| 🛒 **Shopping List** | Categorized, interactive shopping list derived from the meal plan |
| 📊 **Dashboard** | TDEE, macro targets, and BMI analysis |
| 🔄 **Substitutions** | Smart food replacements for allergies and dietary preferences |
| 📚 **Knowledge Base** | DIP Diet guides, nutrition charts, and health documents ingested via RAG |
| 🛡️ **Safety Guardrails** | Blocks harmful medical queries; always shows medical disclaimer |

---

## 🏗️ Architecture

```
Frontend (HTML/CSS/Vanilla JS — Single Page Application)
    ↓  HTTP/REST
FastAPI Backend (Python 3.10+)
    ↓
RAG Pipeline
├── Document Ingestion       — LangChain RecursiveCharacterTextSplitter
├── Embeddings               — sentence-transformers: all-MiniLM-L6-v2
├── Vector Store             — ChromaDB (persistent local)
└── LLM Generation           — IBM Granite via WatsonX.ai API
```

**Demo Mode:** When IBM WatsonX credentials are not configured, the agent automatically falls back to built-in rule-based responses so the full UI can be explored without credentials.

---

## 📁 Project Structure

```
IBM_PR_1/
├── README.md                        # This file
├── DIP_DIET_PLAN.md                 # SDLC plan and project documentation
├── SECURITY.md                      # Security policy and reporting
├── PRIVACY.md                       # Privacy policy and data handling
├── .gitignore                       # Git ignore rules
├── run_project.bat                  # Windows one-click startup script
└── dip_diet_agent/
    ├── backend/
    │   ├── main.py                  # FastAPI application entry point
    │   ├── rag_pipeline.py          # RAG: embed, retrieve, generate
    │   ├── llm_client.py            # IBM Granite LLM client
    │   ├── meal_plan_generator.py   # Structured meal plan generation
    │   ├── shopping_list_generator.py  # Shopping list builder
    │   ├── ingest.py                # Document ingestion pipeline
    │   ├── models.py                # Pydantic data models
    │   └── config.py                # Configuration & environment variables
    ├── frontend/
    │   ├── index.html               # SPA entry point
    │   ├── style.css                # Application styles
    │   └── app.js                   # Frontend JavaScript logic
    ├── data/
    │   ├── knowledge_base/          # Nutrition documents (TXT, MD, CSV)
    │   ├── profiles/                # User profiles (JSON — gitignored)
    │   └── chroma_db/               # ChromaDB vector database (gitignored)
    ├── tests/
    │   └── test_agent.py            # Unit and integration tests
    ├── .env.example                 # Environment variable template
    └── requirements.txt             # Python dependencies
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` inside `dip_diet_agent/` and fill in your IBM WatsonX credentials:

```bash
cd dip_diet_agent
cp .env.example .env    # Linux/macOS
copy .env.example .env  # Windows
```

Edit `.env`:

```env
WATSONX_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

Without credentials the agent runs in **Demo Mode** with built-in responses.

> **Security:** Never commit your actual `.env` file. It is listed in `.gitignore`.

---

## 🛠️ Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/hardikraval-collab/IBM_PR_1.git
cd IBM_PR_1

# 2. Create and activate virtual environment
cd dip_diet_agent
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env      # Windows
# cp .env.example .env      # Linux/macOS
# Edit .env with your credentials (optional for Demo Mode)

# 5. Start the server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + status |
| POST | `/api/profile` | Save or update a user profile |
| GET | `/api/profile/{user_id}` | Retrieve a user profile |
| POST | `/api/chat` | RAG-powered conversational Q&A |
| POST | `/api/meal-plan` | Generate a daily or weekly meal plan |
| POST | `/api/shopping` | Generate a categorized shopping list |
| GET | `/api/dashboard/{user_id}` | Nutrition dashboard (TDEE, macros, BMI) |
| POST | `/api/substitute` | Get food substitution suggestions |
| POST | `/api/ingest` | Ingest a nutrition document (text) |
| POST | `/api/ingest/file` | Upload and ingest a nutrition document file |

Interactive API docs: **http://localhost:8000/api/docs**

---

## 🧪 Testing

```bash
cd dip_diet_agent
python -m pytest tests/ -v
```

Test coverage includes:
- **Configuration** — environment variable loading, demo mode flag
- **Pydantic Models** — UserProfile, ChatRequest, MealPlanRequest validation
- **Meal Plan Generator** — TDEE calculation, macro targets, daily/weekly plans, allergen filtering
- **Shopping List** — list generation, category assignment, allergen exclusion
- **RAG Pipeline** — safety guardrail checks, document ingestion, vector retrieval
- **LLM Client** — demo mode response quality and disclaimer presence

---

## ☁️ Deployment

### Local (Windows)
```bash
run_project.bat
```

### IBM Cloud Code Engine
```bash
# 1. Build Docker image
docker build -t dip-diet-agent .

# 2. Tag and push to IBM Container Registry
ibmcloud cr login
docker tag dip-diet-agent icr.io/<your-namespace>/dip-diet-agent:latest
docker push icr.io/<your-namespace>/dip-diet-agent:latest

# 3. Deploy to Code Engine
ibmcloud ce application create \
  --name dip-diet-agent \
  --image icr.io/<your-namespace>/dip-diet-agent:latest \
  --port 8000 \
  --env-from-secret dip-diet-secrets
```

Set all required environment variables (from `.env.example`) as IBM Secrets Manager secrets or Code Engine environment variables. **Never hardcode credentials.**

---

## ☁️ IBM Technologies

| Technology | Role |
|-----------|------|
| **IBM Granite LLM** | Core language model (`ibm/granite-13b-instruct-v2`) |
| **IBM WatsonX.ai** | LLM API platform |
| **IBM Cloud** | Hosting, Container Registry, Code Engine |
| **IBM Bob** | AI-assisted development and CI/CD |

---

## 🔒 AI Ethics & Safety

- All responses include a medical disclaimer
- Harmful and medical-diagnosis queries are intercepted by safety guardrails
- No Personally Identifiable Information (PII) is sent beyond IBM WatsonX
- Culturally inclusive meal recommendations across dietary traditions
- Bias-free guidance following WHO nutrition principles

---

## 📝 License

MIT License — for educational and demonstration purposes.  
See [LICENSE](LICENSE) for details.
