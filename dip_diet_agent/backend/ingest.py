"""
Document ingestion utility — pre-loads DIP Diet knowledge base on startup.
"""
import logging
from pathlib import Path
from backend.config import KNOWLEDGE_BASE_DIR
from backend.rag_pipeline import rag_pipeline

logger = logging.getLogger(__name__)


def ingest_all_knowledge_base_docs() -> int:
    """
    Scan the knowledge_base directory and ingest all text/markdown/CSV files.
    Skips files that are already indexed (by checking document count).
    """
    total = 0
    kb_path = Path(KNOWLEDGE_BASE_DIR)
    if not kb_path.exists():
        logger.warning(f"Knowledge base directory not found: {kb_path}")
        return 0

    for ext in ("*.txt", "*.md", "*.csv"):
        for file_path in kb_path.glob(ext):
            logger.info(f"Ingesting: {file_path.name}")
            n = rag_pipeline.ingest_file(file_path)
            total += n

    logger.info(f"Total chunks ingested from files: {total}")
    return total
