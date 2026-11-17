"""Simple one-command entrypoint to start the Intelligent Virtual Travel Agent backend.

Usage:
    python run.py
"""

import sys
from pathlib import Path
import uvicorn

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))


def main():
    print("=" * 68)
    print("  Intelligent Virtual Travel Agent — Backend Server")
    print("=" * 68)
    print("  Server URL : http://127.0.0.1:8000")
    print("  Swagger UI : http://127.0.0.1:8000/docs")
    print("  ReDoc      : http://127.0.0.1:8000/redoc")
    print("  Healthcheck: http://127.0.0.1:8000/health")
    print("=" * 68)
    print("  Database   : SQLite (local travel_agent.db)")
    print("  Mode       : Local Development")
    print("=" * 68)
    print("Press CTRL+C to stop the server.\n")

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
