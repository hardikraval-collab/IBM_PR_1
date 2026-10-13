# DIP Diet RAG Agent — Project Plan

## Project Overview

**DIP Diet RAG Agent** is a web-based intelligent nutrition assistant powered by IBM Granite LLM, IBM Cloud, and IBM Bob. It uses Retrieval-Augmented Generation (RAG) to provide personalized diet plans, meal suggestions, and nutrition guidance based on user profiles and a curated knowledge base.

---

## Software Development Lifecycle (SDLC)

### Phase 1 — Requirements Analysis

#### Functional Requirements
- Collect user details: name, age, diet preference, food allergies, medical history, activity level, nutrition goals, city/country
- Ingest DIP Diet resources, nutrition guides, food charts, and health documents
- Semantic search via vector database (ChromaDB)
- RAG-based Q&A with source citations
- Conversational question answering
- Personalized food substitutions
- Daily and weekly meal plans
- Shopping list generation
- Nutrition dashboard

#### Non-Functional Requirements
- Response time < 5 seconds for RAG queries
- Secure storage of user profiles
- AI ethics: helpful, respectful, no harmful medical advice
- Clear medical disclaimer on all outputs
- Safety guardrails on LLM responses

#### Safety & Ethics
- All diet suggestions include a medical disclaimer
- No diagnosis or prescription of medications
- Bias-free recommendations across cultures and dietary traditions
- User data stored locally; no PII sent to third-party APIs beyond IBM Cloud

---

### Phase 2 — System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   DIP Diet RAG Agent                │
├─────────────────────────────────────────────────────┤
│  Frontend (HTML/CSS/JS — Single Page Application)   │
│  ├── User Profile Form                              │
│  ├── Chat Interface                                 │
│  ├── Meal Plan View (Daily / Weekly)                │
│  ├── Shopping List                                  │
│  └── Nutrition Dashboard                            │
├─────────────────────────────────────────────────────┤
│  Backend (FastAPI — Python)                         │
│  ├── /api/profile     — Save user profile           │
│  ├── /api/chat        — RAG conversational Q&A      │
│  ├── /api/meal-plan   — Generate meal plan          │
│  ├── /api/shopping    — Generate shopping list      │
│  ├── /api/substitute  — Food substitution           │
│  └── /api/ingest      — Ingest knowledge docs       │
├─────────────────────────────────────────────────────┤
│  RAG Pipeline                                       │
│  ├── Document Loader (PDF, TXT, MD)                 │
│  ├── Text Chunker (RecursiveCharacterTextSplitter)  │
│  ├── Embeddings (IBM Granite / sentence-transformers)│
│  └── Vector Store (ChromaDB)                        │
├─────────────────────────────────────────────────────┤
│  IBM Granite LLM (via IBM WatsonX / ibm-generative-ai)│
└─────────────────────────────────────────────────────┘
```

#### Technology Stack
| Layer | Technology |
|-------|-----------|
| LLM | IBM Granite (ibm-granite/granite-13b-instruct-v2 via WatsonX) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | ChromaDB (local persistent) |
| Backend | FastAPI + Python 3.10+ |
| Frontend | HTML5 / CSS3 / Vanilla JS |
| Document Loader | LangChain document loaders |
| Deployment | Uvicorn (local), IBM Cloud Code Engine (cloud) |
| Package Manager | pip + requirements.txt |

---

### Phase 3 — Design

#### Data Flow
1. User fills profile form → stored in `data/profiles/{user_id}.json`
2. Admin ingests nutrition docs → chunked + embedded → ChromaDB
3. User asks a question → query embedded → top-k docs retrieved → prompt constructed → Granite LLM generates answer with citations
4. Meal plan requested → profile + retrieved docs → structured meal plan generated
5. Shopping list derived from meal plan items

#### Prompt Engineering
- System prompt enforces: DIP Diet expert persona, medical disclaimer, citation format
- User profile injected as context prefix
- Retrieved chunks appended as `[SOURCE N]` references
- Safety guardrail keywords trigger disclaimer injection

---

### Phase 4 — Implementation

#### Directory Structure
```
dip_diet_agent/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── rag_pipeline.py      # RAG: embedding, retrieval, generation
│   ├── llm_client.py        # IBM Granite LLM client
│   ├── ingest.py            # Document ingestion pipeline
│   ├── models.py            # Pydantic data models
│   └── config.py            # Configuration & environment variables
├── frontend/
│   ├── index.html           # Main SPA
│   ├── style.css            # Styles
│   └── app.js               # Frontend logic
├── data/
│   ├── knowledge_base/      # Nutrition docs (PDF, TXT, MD)
│   ├── profiles/            # User profiles (JSON)
│   └── chroma_db/           # ChromaDB persistent storage
├── docs/
│   └── sample_nutrition.txt # Sample DIP Diet knowledge base docs
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
├── DIP_DIET_PLAN.md         # This file
└── run_project.bat          # Windows startup script
```

---

### Phase 5 — Testing

| Test Type | Coverage |
|-----------|----------|
| Unit Tests | RAG pipeline, LLM client, models |
| Integration Tests | API endpoints, vector DB queries |
| UI Tests | Form submission, chat flow |
| Safety Tests | Harmful query guardrails |
| Performance Tests | Response latency < 5s |

---

### Phase 6 — Deployment

#### Local Deployment
```bash
run_project.bat
```

#### IBM Cloud Deployment
1. Build Docker image: `docker build -t dip-diet-agent .`
2. Push to IBM Container Registry
3. Deploy to IBM Cloud Code Engine
4. Configure environment variables via IBM Secrets Manager

---

### Phase 7 — Maintenance & Ethics

- Regular re-ingestion of updated nutrition guidelines
- LLM model version pinning with upgrade path
- User feedback loop for improving recommendations
- Monthly review of safety guardrails
- Compliance with GDPR / data privacy regulations

---

## Medical Disclaimer

> **⚕️ IMPORTANT MEDICAL DISCLAIMER:** The DIP Diet RAG Agent provides general nutrition information for educational purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider or registered dietitian before making significant changes to your diet, especially if you have a medical condition, are pregnant, or are taking medications. The creators of this tool assume no liability for health outcomes resulting from the use of this application.

---

## About DIP Diet

The **DIP (Discipline Intermittent Protocol) Diet** is a structured nutrition framework emphasizing:
- Disciplined meal timing and portion control
- Intermittent fasting windows aligned with circadian rhythm
- Plant-forward, whole-food nutrition
- Personalized macronutrient targets based on activity level and goals

---

## IBM Technologies Used

| Technology | Purpose |
|-----------|---------|
| IBM Granite LLM | Core language model for generation |
| IBM WatsonX.ai | LLM API platform |
| IBM Cloud | Hosting and deployment |
| IBM Bob | Development assistant and CI/CD |

---

## License

This project is developed for educational and demonstration purposes under the MIT License.
