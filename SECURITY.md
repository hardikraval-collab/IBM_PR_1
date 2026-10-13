# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x (current) | ✅ Yes |

---

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please **do not** open a public GitHub issue.

Instead, report it privately:

1. **Email:** Open a private GitHub Security Advisory at  
   `https://github.com/hardikraval-collab/IBM_PR_1/security/advisories/new`
2. Include a clear description of the vulnerability, reproduction steps, and potential impact.
3. You will receive an acknowledgement within **48 hours** and a resolution update within **7 days**.

---

## Security Design Principles

### Secrets Management

- **IBM Cloud API keys, WatsonX credentials, and all secrets** are stored exclusively in `.env` files, which are listed in `.gitignore` and are **never committed to the repository**.
- The repository contains only `.env.example` with placeholder values — no real credentials.
- For production deployments, credentials must be injected via environment variables, IBM Secrets Manager, or Cloud Code Engine secrets — never hardcoded.

### User Data

- User profiles are stored as local JSON files in `data/profiles/` which is excluded from version control via `.gitignore`.
- No personal health data, dietary information, or user profiles are stored in the repository or transmitted to any service other than IBM WatsonX.ai for LLM generation.
- The ChromaDB vector database (`data/chroma_db/`) stores only de-identified nutrition document embeddings and is also excluded from the repository.

### API Security

- The FastAPI backend validates all input via **Pydantic models** with strict type enforcement.
- File upload endpoints accept only `.txt`, `.md`, and `.csv` file types to prevent arbitrary file upload attacks.
- CORS is configured to restrict cross-origin requests in production environments.

### LLM Safety Guardrails

- All user queries are checked against a list of safety keywords before being forwarded to the LLM.
- Queries related to medical diagnosis, prescriptions, or harmful content trigger a safety response that redirects the user to professional healthcare.
- All LLM responses are appended with a mandatory medical disclaimer.

### Dependency Security

- All Python dependencies are pinned to specific versions in `requirements.txt`.
- Regularly audit dependencies with `pip audit` or `safety check`.
- The virtual environment (`venv/`) is excluded from the repository.

---

## IBM Cloud Security

When deploying to IBM Cloud:

- Use **IBM Secrets Manager** to store and rotate API keys.
- Enable **IBM Cloud Activity Tracker** for audit logging.
- Configure **IBM Cloud Security and Compliance Center** policies.
- Use **IBM Container Registry** with Vulnerability Advisor for Docker image scanning.
- Restrict Code Engine application access using IBM Cloud IAM policies.

---

## Responsible Disclosure

This project is developed for educational purposes. We value the security research community and will acknowledge all valid, responsibly disclosed vulnerabilities.
