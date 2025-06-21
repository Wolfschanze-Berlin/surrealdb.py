#!/usr/bin/env python3
"""
Startup script for FastAPI SurrealDB Auth Example
"""

import uvicorn
import os
from config import settings

if __name__ == "__main__":
    print("🚀 Starting FastAPI SurrealDB Auth Example")
    print(f"📊 Debug mode: {settings.DEBUG}")
    print(f"🔗 SurrealDB URL: {settings.SURREALDB_URL}")
    print(f"📝 Access the API docs at: http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )