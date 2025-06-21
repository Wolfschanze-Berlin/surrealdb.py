from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_database, db_manager
from routers import auth, users, profiles
from config import settings
from logger import get_logger, log_api_request
import time

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    try:
        await init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
    
    yield
    
    # Shutdown
    await db_manager.disconnect()
    print("Database connection closed")

app = FastAPI(
    title=settings.APP_NAME,
    description="A complete FastAPI authentication and CRUD example using SurrealDB",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profiles.router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to FastAPI SurrealDB Auth Example",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        db = await db_manager.connect()
        # Simple query to check database connectivity
        await db.query("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )