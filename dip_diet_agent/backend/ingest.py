"""
Document ingestion utility — pre-loads DIP Diet knowledge base on startup.
"""
import logging
from pathlib import Path
from backend.config import KNOWLEDGE_BASE_DIR
from backend.rag_pipeline import rag_pipeline

logger = logging.getLogger(__name__)


def _already_indexed(source_name: str) -> bool:
    """Return True if any document with this source is already in the collection."""
    try:
        results = rag_pipeline.collection.get(
            where={"source": source_name},
            limit=1,
        )
        return len(results.get("ids", [])) > 0
    except Exception:
        return False


def ingest_all_knowledge_base_docs() -> int:
    """
    Scan the knowledge_base directory and ingest all text/markdown/CSV files.
    Skips files whose source name is already present in the vector store.
    This prevents duplicate embeddings when the service restarts with a
    persistent ChromaDB (local dev) while still re-ingesting on a fresh
    ephemeral /tmp directory (Render free tier).
    """
    total = 0
    kb_path = Path(KNOWLEDGE_BASE_DIR)
    if not kb_path.exists():
        logger.warning(f"Knowledge base directory not found: {kb_path}")
        return 0

    for ext in ("*.txt", "*.md", "*.csv"):
        for file_path in kb_path.glob(ext):
            if _already_indexed(file_path.name):
                logger.info(f"Already indexed, skipping: {file_path.name}")
                continue
            logger.info(f"Ingesting: {file_path.name}")
            n = rag_pipeline.ingest_file(file_path)
            total += n

    logger.info(f"Total chunks ingested from files: {total}")
    return total
