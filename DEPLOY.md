# Deployment Guide — DIP Diet RAG Agent

This guide walks you through deploying the DIP Diet RAG Agent to **Render** (free tier) so you can share a public HTTPS URL with friends.

---

## Architecture Overview

```
Browser → https://dip-diet-rag-agent.onrender.com/
              │
              └── Render Web Service (Python)
                    ├── FastAPI backend  (API routes at /api/*)
                    ├── Vanilla JS frontend  (served at / via StaticFiles)
                    ├── ChromaDB  (ephemeral in /tmp on Render free tier)
                    ├── sentence-transformers  (all-MiniLM-L6-v2, local)
                    └── IBM watsonx.ai  (Granite LLM, called over HTTPS)
```

**One service. One URL. No Vercel required.**  
The FastAPI app serves both the API and the frontend HTML/JS/CSS from the same origin, so no cross-origin configuration is needed.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| GitHub account | Repo must be public or Render must be connected |
| Render account | Free at https://render.com |
| IBM Cloud account | For watsonx.ai credentials (optional — app works in demo mode without them) |

---

## Step 1 — Push the code to GitHub

Make sure the repository is pushed:

```bash
git add .
git commit -m "chore: add Render deployment configuration"
git push origin main
```

**Verify** `.env` is **not** committed (`git status` should not show it). The `.gitignore` already excludes it.

---

## Step 2 — Create a Render Web Service

1. Go to **https://render.com** and sign in.
2. Click **New +** → **Web Service**.
3. Connect your GitHub account and select this repository.
4. Render will auto-detect `render.yaml` at the repo root and pre-fill all settings. If it doesn't, fill in manually:

| Setting | Value |
|---|---|
| **Name** | `dip-diet-rag-agent` |
| **Region** | Oregon (or nearest to you) |
| **Branch** | `main` |
| **Root Directory** | `dip_diet_agent` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install --upgrade pip && pip install -r requirements.txt` |
| **Start Command** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info` |
| **Plan** | Free |

5. Click **Create Web Service** (do not deploy yet — add env vars first).

---

## Step 3 — Set Environment Variables in Render Dashboard

Go to your service → **Environment** tab → **Add Environment Variable** for each:

### Required (IBM watsonx.ai — for full IBM Granite LLM mode)

| Key | Value | Where to find it |
|---|---|---|
| `WATSONX_API_KEY` | `your-api-key` | https://cloud.ibm.com/iam/apikeys |
| `WATSONX_PROJECT_ID` | `your-project-id` | WatsonX.ai Studio → Project → Settings → General |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | Default; change region if needed |
| `GRANITE_MODEL_ID` | `ibm/granite-13b-instruct-v2` | Or `ibm/granite-3-8b-instruct` |

> **Without these variables**, the app still works in **Demo Mode** — it uses smart rule-based responses instead of the IBM Granite LLM. Users will see "Demo Mode" in the status badge.

### Recommended (already in render.yaml with defaults)

| Key | Value |
|---|---|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` |
| `DEBUG` | `false` |
| `CHUNK_SIZE` | `512` |
| `CHUNK_OVERLAP` | `64` |
| `TOP_K_RESULTS` | `4` |
| `LLM_MAX_NEW_TOKENS` | `800` |
| `LLM_TEMPERATURE` | `0.7` |

> **Security**: Render encrypts secret environment variables. They are never visible in logs or to other users. Never paste credentials into your code or commit them to Git.

---

## Step 4 — Deploy

Click **Manual Deploy** → **Deploy latest commit**.

Watch the build logs. A successful build looks like:

```
==> Running build command: pip install --upgrade pip && pip install -r requirements.txt
...
Successfully installed fastapi-0.143.0 chromadb-0.6.3 ibm-watsonx-ai-1.8.0 ...

==> Starting service with: uvicorn backend.main:app ...
INFO: DIP Diet RAG Agent starting up...
INFO: Ingesting: dip_diet_nutrition_guide.txt
INFO: Ingesting: food_nutrition_chart.txt
...
INFO: Knowledge base ready. Total chunks: 312
INFO: Application startup complete.
```

**First deploy takes ~5–8 minutes** (downloading sentence-transformers model ~90 MB).

---

## Step 5 — Get your public URL

After deploy succeeds, Render shows:

```
Your service is live at: https://dip-diet-rag-agent.onrender.com
```

(The exact subdomain may differ if the name was taken — Render will show you the actual URL.)

**Test the health endpoint:**
```
https://dip-diet-rag-agent.onrender.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "mode": "production",
  "knowledge_base_chunks": 312,
  "llm_model": "IBM Granite (WatsonX)"
}
```

---

## Step 6 — Share with friends

Share the URL:
```
https://dip-diet-rag-agent.onrender.com
```

Friends can:
1. Fill in their profile (no account needed)
2. Ask nutrition questions in the RAG chat
3. Generate weekly meal plans
4. Get shopping lists and food substitutions
5. View their nutrition dashboard

---

## Storage Behaviour on Render Free Tier

| Data | Storage | Persistence |
|---|---|---|
| Knowledge base `.txt` files | Git repo (committed) | ✅ Permanent — served from the repo |
| ChromaDB vector embeddings | `/tmp/dip_diet/chroma_db/` | ⚠️ Wiped on restart — **re-ingested automatically** on startup from knowledge base files |
| User profiles (JSON) | `/tmp/dip_diet/profiles/` | ⚠️ Wiped on restart — users re-enter profile |

### Upgrading to Persistent Storage

For production use, upgrade to **Render Starter plan ($7/mo)** and add a **Persistent Disk**:

1. In Render dashboard → your service → **Disks** → **Add Disk**
2. Mount path: `/data`
3. In Render **Environment**, add:
   ```
   RENDER_PERSISTENT_DATA=true
   ```
4. Update `config.py` `_WRITABLE_ROOT` to `Path("/data")` when this var is set.

Alternatively, use **ChromaDB Cloud** or **Pinecone** for the vector store.

---

## Local Development

```bash
cd dip_diet_agent
cp .env.example .env       # Fill in WATSONX_API_KEY and WATSONX_PROJECT_ID
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Build fails: `No module named 'backend'` | Confirm **Root Directory** is `dip_diet_agent` in Render |
| Service shows "Offline" | Check `/api/health` — may be a cold start (free tier sleeps after 15 min inactivity) |
| "Demo Mode" in status badge | `WATSONX_API_KEY` or `WATSONX_PROJECT_ID` not set in Render environment |
| 500 error on `/api/chat` | Check Render logs for WatsonX auth error; verify API key and project ID |
| Slow first response | Render free tier cold-starts take ~30 s; click the link once to wake it up |
| Profile lost between sessions | Expected on free tier (ephemeral `/tmp`); upgrade to persistent disk to keep profiles |

---

## Environment Variable Reference

| Variable | Default | Description |
|---|---|---|
| `WATSONX_API_KEY` | — | IBM Cloud API key for WatsonX.ai |
| `WATSONX_PROJECT_ID` | — | WatsonX.ai project ID |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | WatsonX.ai regional endpoint |
| `GRANITE_MODEL_ID` | `ibm/granite-13b-instruct-v2` | IBM Granite model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace sentence-transformers model |
| `CHUNK_SIZE` | `512` | Token chunk size for RAG ingestion |
| `CHUNK_OVERLAP` | `64` | Token overlap between chunks |
| `TOP_K_RESULTS` | `4` | Number of RAG results to retrieve |
| `LLM_MAX_NEW_TOKENS` | `800` | Max tokens per LLM response |
| `LLM_TEMPERATURE` | `0.7` | LLM generation temperature |
| `DEBUG` | `false` | Enable uvicorn auto-reload (dev only) |
| `ALLOWED_ORIGINS` | `*` | CORS origins (leave `*` for same-origin serving) |
| `RENDER` | set by Render | Auto-detected; triggers `/tmp` path for writable data |
