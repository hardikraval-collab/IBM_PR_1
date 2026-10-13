"""
RAG Pipeline: Document ingestion, embedding, vector search, and generation.
"""
import logging
import uuid
from typing import List, Tuple
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import (
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS,
    MEDICAL_DISCLAIMER,
    SAFETY_KEYWORDS,
    SAFETY_RESPONSE,
)
from backend.llm_client import llm_client
from backend.models import SourceCitation

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    End-to-end Retrieval-Augmented Generation pipeline for DIP Diet Agent.
    """

    def __init__(self):
        # ── Embedding Model ───────────────────────────────────────────────────
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

        # ── ChromaDB Vector Store ─────────────────────────────────────────────
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB collection '{CHROMA_COLLECTION_NAME}' ready. "
            f"Documents: {self.collection.count()}"
        )

        # ── Text Splitter ─────────────────────────────────────────────────────
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""],
        )

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest_text(self, content: str, title: str, source_name: str) -> int:
        """
        Ingest a text document into the vector store.

        Args:
            content: Raw document text.
            title: Human-readable document title.
            source_name: Short source identifier for citations.

        Returns:
            Number of chunks ingested.
        """
        chunks = self.text_splitter.split_text(content)
        if not chunks:
            logger.warning(f"No chunks generated for '{title}'")
            return 0

        embeddings = self.embedder.encode(chunks, show_progress_bar=False).tolist()
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {"source": source_name, "title": title, "chunk_index": i}
            for i, _ in enumerate(chunks)
        ]

        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )
        logger.info(f"Ingested {len(chunks)} chunks from '{title}'")
        return len(chunks)

    def ingest_file(self, file_path: Path) -> int:
        """Ingest a file from the knowledge base directory."""
        try:
            content = file_path.read_text(encoding="utf-8")
            return self.ingest_text(
                content=content,
                title=file_path.stem.replace("_", " ").title(),
                source_name=file_path.name,
            )
        except Exception as exc:
            logger.error(f"Failed to ingest {file_path}: {exc}")
            return 0

    def ingest_all_documents(self) -> int:
        """Ingest all documents in the knowledge base directory."""
        total = 0
        kb_dir = Path(CHROMA_DB_DIR).parent / "knowledge_base"
        for ext in ("*.txt", "*.md", "*.csv"):
            for file_path in kb_dir.glob(ext):
                total += self.ingest_file(file_path)
        return total

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Tuple[str, dict, float]]:
        """
        Retrieve the most relevant document chunks for a query.

        Returns:
            List of (document_text, metadata, distance_score) tuples.
        """
        if self.collection.count() == 0:
            return []

        query_embedding = self.embedder.encode([query], show_progress_bar=False).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            retrieved.append((doc, meta, dist))

        return retrieved

    # ── Safety Check ─────────────────────────────────────────────────────────

    def is_safe_query(self, query: str) -> bool:
        """Check if query contains safety-sensitive keywords requiring guardrail."""
        query_lower = query.lower()
        return not any(kw in query_lower for kw in SAFETY_KEYWORDS)

    # ── RAG Generation ────────────────────────────────────────────────────────

    def generate_rag_response(
        self,
        query: str,
        user_profile: dict = None,
        conversation_history: list = None,
    ) -> Tuple[str, List[SourceCitation], bool]:
        """
        Full RAG pipeline: retrieve → build prompt → generate → return response.

        Args:
            query: User question.
            user_profile: Dict of user profile details for personalisation.
            conversation_history: Previous chat turns for context.

        Returns:
            (response_text, source_citations, is_safe)
        """
        # Safety guardrail
        if not self.is_safe_query(query):
            return SAFETY_RESPONSE, [], False

        # Retrieve relevant context
        retrieved = self.retrieve(query)
        sources: List[SourceCitation] = []
        context_blocks = []

        for i, (doc, meta, dist) in enumerate(retrieved):
            relevance = max(0.0, 1.0 - dist)
            sources.append(
                SourceCitation(
                    source=meta.get("source", "DIP Diet Knowledge Base"),
                    excerpt=doc[:200] + ("..." if len(doc) > 200 else ""),
                    relevance_score=round(relevance, 3),
                )
            )
            context_blocks.append(f"[SOURCE {i+1}] ({meta.get('title', 'Unknown')})\n{doc}")

        context_text = (
            "\n\n".join(context_blocks)
            if context_blocks
            else "No specific documents retrieved. Answer using general DIP Diet knowledge."
        )

        # Build personalised user context
        profile_context = self._build_profile_context(user_profile)

        # Build conversation history context
        history_context = ""
        if conversation_history:
            history_lines = []
            for turn in conversation_history[-4:]:  # Last 4 turns
                role = "User" if turn.get("role") == "user" else "Assistant"
                history_lines.append(f"{role}: {turn.get('content', '')}")
            history_context = "Previous conversation:\n" + "\n".join(history_lines) + "\n\n"

        # Construct final prompt
        prompt = (
            f"{profile_context}"
            f"{history_context}"
            f"Retrieved nutrition knowledge:\n{context_text}\n\n"
            f"User question: {query}\n\n"
            f"Provide a helpful, accurate, and personalised DIP Diet response. "
            f"Cite sources as [SOURCE N] where relevant. "
            f"End with a brief medical disclaimer."
        )

        response = llm_client.generate(prompt)

        # Ensure disclaimer is present
        if MEDICAL_DISCLAIMER[:30] not in response and "DISCLAIMER" not in response.upper():
            response += f"\n\n_{MEDICAL_DISCLAIMER}_"

        return response, sources, True

    @staticmethod
    def _build_profile_context(profile: dict = None) -> str:
        """Build a user profile context string for the LLM prompt."""
        if not profile:
            return ""
        parts = [f"User profile:"]
        if profile.get("name"):
            parts.append(f"- Name: {profile['name']}")
        if profile.get("age"):
            parts.append(f"- Age: {profile['age']}")
        if profile.get("diet_preference"):
            parts.append(f"- Diet: {profile['diet_preference']}")
        if profile.get("food_allergies"):
            allergies = ", ".join(profile["food_allergies"])
            parts.append(f"- Allergies: {allergies}")
        if profile.get("medical_history"):
            conditions = ", ".join(profile["medical_history"])
            parts.append(f"- Medical history: {conditions}")
        if profile.get("activity_level"):
            parts.append(f"- Activity level: {profile['activity_level']}")
        if profile.get("nutrition_goals"):
            goals = ", ".join(profile["nutrition_goals"])
            parts.append(f"- Goals: {goals}")
        if profile.get("location"):
            loc = profile["location"]
            city = loc.get("city", "") if isinstance(loc, dict) else getattr(loc, "city", "")
            country = loc.get("country", "") if isinstance(loc, dict) else getattr(loc, "country", "")
            parts.append(f"- Location: {city}, {country}")
        return "\n".join(parts) + "\n\n"

    # ── Meal Plan Generation ──────────────────────────────────────────────────

    def generate_meal_plan_prompt(self, user_profile: dict, plan_type: str = "weekly") -> str:
        """Generate a prompt for meal plan creation."""
        profile_ctx = self._build_profile_context(user_profile)
        retrieved = self.retrieve(
            f"{user_profile.get('diet_preference', 'vegetarian')} meal plan nutrition",
            top_k=3,
        )
        context = "\n\n".join(doc for doc, _, _ in retrieved)

        days = "1 day" if plan_type == "daily" else "7 days (Monday to Sunday)"
        return (
            f"{profile_ctx}"
            f"Relevant nutrition knowledge:\n{context}\n\n"
            f"Create a detailed {days} DIP Diet meal plan for this user including "
            f"breakfast, lunch, dinner, and 1-2 snacks per day. "
            f"For each meal include: name, ingredients, approximate calories, protein (g), carbs (g), fat (g), "
            f"and a brief preparation note. "
            f"Respect the user's diet preference ({user_profile.get('diet_preference', 'vegetarian')}), "
            f"allergies, medical conditions, and nutrition goals. "
            f"Format clearly with day headings. "
            f"End with a medical disclaimer."
        )

    def generate_substitution_prompt(
        self, food_item: str, reason: str, user_profile: dict
    ) -> str:
        """Generate a prompt for food substitution."""
        profile_ctx = self._build_profile_context(user_profile)
        retrieved = self.retrieve(f"food substitution alternative {food_item}", top_k=2)
        context = "\n\n".join(doc for doc, _, _ in retrieved)

        return (
            f"{profile_ctx}"
            f"Relevant knowledge:\n{context}\n\n"
            f"Suggest 3-5 healthy substitutions for '{food_item}' "
            f"(reason: {reason or 'personal preference'}). "
            f"For each substitution, explain the nutritional difference and how to use it in DIP Diet cooking. "
            f"Consider the user's dietary preference and allergies."
        )


# Singleton instance
rag_pipeline = RAGPipeline()
