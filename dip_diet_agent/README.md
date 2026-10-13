# DIP Diet RAG Agent

> **Personalized nutrition assistant powered by IBM Granite LLM, IBM Cloud, and IBM Bob.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![IBM Granite](https://img.shields.io/badge/IBM-Granite%20LLM-1a56db)](https://www.ibm.com/products/watsonx-ai)
[![ChromaDB](https://img.shields.io/badge/Vector%20DB-ChromaDB-orange)](https://trychroma.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ⚕️ Medical Disclaimer

> This application provides general nutrition information for **educational purposes only**. It is **NOT** a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider or registered dietitian before making significant dietary changes.

---

## 🚀 Quick Start (Windows)

```bash
# From the project root (d:\PR_1):
run_project.bat
```

Then open your browser at **http://localhost:8000**

---

## 🥗 Features

| Feature | Description |
|---------|-------------|
| 👤 **User Profile** | Personalized setup: age, diet, allergies, medical history, goals, location |
| 💬 **RAG Q&A Chat** | Nutrition questions answered using retrieved documents + IBM Granite |
| 📅 **Meal Plans** | Daily and weekly plans tailored to your profile |
| 🛒 **Shopping List** | Categorized, interactive shopping list from your meal plan |
| 📊 **Dashboard** | TDEE, macro targets, BMI analysis |
| 🔄 **Substitutions** | Smart food replacements for allergies & preferences |
| 📚 **Knowledge Base** | DIP Diet guides, nutrition charts, health documents ingested via RAG |
| 🛡️ **Safety Guardrails** | Blocks harmful medical queries; always shows disclaimer |

---

## 🏗️ Architecture

```
Frontend (HTML/CSS/JS SPA)
    ↓
FastAPI Backend (Python)
    ↓
RAG Pipeline
├── Document Ingestion (LangChain text splitter)
├── Embeddings (sentence-transformers: all-MiniLM-L6-v2)
├── Vector Store (ChromaDB — persistent local)
└── LLM Generation (IBM Granite via WatsonX.ai)
```

---

## 📁 Project Structure

```
dip_diet_agent/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── rag_pipeline.py          # RAG: embed, retrieve, generate
│   ├── llm_client.py            # IBM Granite LLM client
│   ├── meal_plan_generator.py   # Structured meal plan generation
│   ├── shopping_list_generator.py # Shopping list builder
│   ├── ingest.py                # Document ingestion
│   ├── models.py                # Pydantic data models
│   └── config.py                # Configuration
├── frontend/
│   ├── index.html               # SPA
│   ├── style.css                # Styles
│   └── app.js                   # Frontend logic
├── data/
│   ├── knowledge_base/          # Nutrition documents
│   ├── profiles/                # User profiles (JSON)
│   └── chroma_db/               # Vector database
├── tests/
│   └── test_agent.py            # Unit tests
├── .env.example                 # Environment variable template
└── requirements.txt             # Python dependencies
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in your IBM WatsonX credentials:

```env
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

Without credentials, the agent runs in **Demo Mode** with built-in responses.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + status |
| POST | `/api/profile` | Save user profile |
| GET | `/api/profile/{user_id}` | Get user profile |
| POST | `/api/chat` | RAG Q&A chat |
| POST | `/api/meal-plan` | Generate meal plan |
| POST | `/api/shopping` | Generate shopping list |
| GET | `/api/dashboard/{user_id}` | Nutrition dashboard |
| POST | `/api/substitute` | Food substitutions |
| POST | `/api/ingest` | Ingest document |
| POST | `/api/ingest/file` | Upload and ingest file |

API docs: **http://localhost:8000/api/docs**

---

## 🧪 Running Tests

```bash
cd dip_diet_agent
python -m pytest tests/ -v
```

---

## 🛠️ Manual Installation

```bash
cd dip_diet_agent
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔒 AI Ethics & Safety

- All responses include a medical disclaimer
- Harmful/medical queries are intercepted by safety guardrails
- No PII sent to external services beyond IBM WatsonX
- Culturally inclusive meal recommendations
- Bias-free dietary guidance

---

## ☁️ IBM Technologies

| Technology | Role |
|-----------|------|
| **IBM Granite LLM** | Core language model (ibm/granite-13b-instruct-v2) |
| **IBM WatsonX.ai** | LLM API platform |
| **IBM Cloud** | Hosting and deployment |
| **IBM Bob** | Development assistant |

---

## 📝 License

MIT License — for educational and demonstration purposes.
