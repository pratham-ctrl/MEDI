"""FastAPI main application"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import time
from app.config import settings
from app.api.routes import auth, chat, documents, drugs, profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()

# Create FastAPI app
app = FastAPI(
    title="Medical Chatbot API",
    description="Multi-Agent Medical Chatbot Backend with RAG",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True,
    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (time.time() - start_time) * 1000
    
    # Log
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.2f}ms"
    )
    
    return response


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Medical Chatbot API",
        "docs": "/api/docs",
        "health": "/health"
    }


# Include routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["Chat"]
)

app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["Documents"]
)

app.include_router(
    drugs.router,
    prefix="/api/v1/drugs",
    tags=["Drugs"]
)

app.include_router(
    profile.router,
    prefix="/api/v1/profile",
    tags=["Profile"]
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Medical Chatbot API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize services (connection pooling, etc.)
    # This will be done lazily when services are first accessed
    
    logger.info("Medical Chatbot API started successfully!")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Medical Chatbot API...")
    
    # Close connections, cleanup resources
    # Services will handle their own cleanup
    
    logger.info("Medical Chatbot API shut down successfully!")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
