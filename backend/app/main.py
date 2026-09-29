"""
Main FastAPI entry point for Canary Deployment Simulator (P71).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="A Cloud-Based Canary Deployment Simulator with automated traffic shifting and rollback.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
def root():
    """Root endpoint verifying API availability."""
    return {
        "project": settings.APP_NAME,
        "project_id": settings.PROJECT_ID,
        "status": "operational",
        "version": "1.0.0"
    }


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for compute and container orchestrators."""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV
    }
