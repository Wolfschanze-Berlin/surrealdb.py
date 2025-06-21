from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from chat_service import ChatService
from routers import chat
from database import init_database, db_manager
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    try:
        await init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
    
    print("ChatGPT API service starting up...")
    
    yield
    
    # Shutdown
    await db_manager.disconnect()
    print("ChatGPT API service shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="A FastAPI application with OpenAI ChatGPT integration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to ChatGPT FastAPI Integration",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "chatgpt-api",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )