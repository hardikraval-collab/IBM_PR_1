# Privacy Policy

**DIP Diet RAG Agent** — Privacy Policy  
*Last updated: July 2025*

---

## Overview

The DIP Diet RAG Agent is an educational nutrition assistant. This policy describes what data is collected, how it is used, and how it is protected.

---

## Data We Collect

### User Profile Data
When you create a profile, the following information is collected and stored locally:

| Field | Purpose |
|-------|---------|
| Name | Personalizing responses |
| Age, gender, weight, height | Calculating TDEE and BMI |
| Diet preference | Filtering meal plans and suggestions |
| Food allergies | Excluding allergens from recommendations |
| Medical history | Contextualizing nutrition advice |
| Activity level | Calculating calorie targets |
| Nutrition goals | Tailoring recommendations |
| City / country | Regional food recommendations |

> **⚕️ Medical Notice:** Medical history you enter is used solely to tailor nutritional guidance. This application does not diagnose, treat, or prescribe. Always consult a qualified healthcare provider.

### Chat History
- Conversation history is held **in-memory in your browser session only**.
- It is sent to the backend to provide conversational context for each query.
- It is **not persisted** to disk on the server beyond the active session.

---

## Where Data Is Stored

| Data | Storage Location |
|------|-----------------|
| User profiles | Local JSON files on the server running the agent (`data/profiles/`) |
| Vector embeddings | Local ChromaDB on the server (`data/chroma_db/`) — contains only nutrition document text, not personal data |
| Chat messages (during inference) | Sent to IBM WatsonX.ai API for LLM generation |
| Logs | Local server log files |

**No user data is stored in the GitHub repository.** All personal data directories are listed in `.gitignore`.

---

## Data Sharing

| Recipient | What Is Shared | Purpose |
|-----------|---------------|---------|
| **IBM WatsonX.ai** | Query text + user profile context (name, diet, goals) | LLM generation |
| **No other third parties** | Nothing | N/A |

IBM WatsonX.ai processes data in accordance with [IBM's Privacy Policy](https://www.ibm.com/privacy).

---

## Data Retention

- **User profiles** are retained until you delete them or the local server data is cleared.
- **Chat history** is session-based and not persisted on the server.
- **Logs** are stored locally and should be cleared periodically.

---

## Your Rights

You have the right to:

- **Access** your stored profile data at any time via `GET /api/profile/{user_id}`.
- **Delete** your profile by removing the corresponding file from `data/profiles/`.
- **Not provide** optional fields such as medical history or weight — the agent will still function.

---

## Children's Privacy

This application is intended for adults aged 18 and older. It is not designed to collect data from minors.

---

## Security Measures

- Profile data is stored locally and not transmitted to external services except as noted above.
- No IBM Cloud API keys or passwords are stored in the repository.
- All secrets are managed via environment variables. See [SECURITY.md](SECURITY.md) for full details.

---

## Changes to This Policy

This policy may be updated as the project evolves. Changes will be committed to this file with a dated entry.

---

## Contact

For privacy concerns, open a GitHub issue or Security Advisory at  
https://github.com/hardikraval-collab/IBM_PR_1/issues

---

## Disclaimer

> The DIP Diet RAG Agent is an educational tool. It does not constitute medical advice. The nutritional guidance provided is general in nature and should not replace consultation with a qualified healthcare professional or registered dietitian.
