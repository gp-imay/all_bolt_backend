# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import logging
import time

from app.config import settings
from app.database import engine, Base
from app.models import users, script  # This ensures models are imported for migrations

# Import routers
from app.routers import users, scripts, test_beats, beats, scenes, scene_descriptions, scene_segments

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "Invalid request parameters"
        }
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "detail": "A database error occurred"
        }
    )

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "api_version": "v1"
    }

# Root endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Welcome to Movie Script Manager API",
        "documentation": f"{settings.API_V1_PREFIX}/docs"
    }

## Include routers
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["users"]
)

app.include_router(
    scripts.router,
    prefix=f"{settings.API_V1_PREFIX}/scripts",
    tags=["scripts"]
)

app.include_router(
    beats.router,
    prefix=f"{settings.API_V1_PREFIX}/beats",
    tags=["beats"]
)

app.include_router(
    scenes.router,
    prefix=f"{settings.API_V1_PREFIX}/scenes",
    tags=["scenes"]
)

app.include_router(
    scene_descriptions.router,
    prefix=f"{settings.API_V1_PREFIX}/scene-descriptions",
    tags=["scene-descriptions"]
)

app.include_router(
    scene_segments.router,
    prefix=f"{settings.API_V1_PREFIX}/scene-segments",
    tags=["scene-segments"]
)

if settings.DEBUG:  # Only include test endpoints in debug mode
    app.include_router(
        test_beats.router,
        prefix=f"{settings.API_V1_PREFIX}/test",
        tags=["test"]
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Movie Script Manager API")
    # Add any startup tasks here (e.g., database connection verification)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Movie Script Manager API")
    # Add any cleanup tasks here

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )