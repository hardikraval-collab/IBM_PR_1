"""
Standalone server start script — writes log to server.log
"""
import sys
import logging
from pathlib import Path

# Add parent to sys.path so 'backend' package is found
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("server.log", mode="w", encoding="utf-8"),
        ]
    )
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
    )
