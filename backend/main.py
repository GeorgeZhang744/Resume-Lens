"""
Application entry point.

Run with: uvicorn main:app --reload
(from the backend directory)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import app.config  # noqa: F401 — load .env before routes/services use settings
from app.api.routes import api_router, root_router
from app.config import ALLOWED_ORIGINS
from app.limiter import limiter

# Create the FastAPI application instance
app = FastAPI(title="AI Job Match Agent")

# Rate limiting — in-memory, per IP
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: allow the frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes at / and /health
app.include_router(root_router)

# API namespace at /api
app.include_router(api_router, prefix="/api")
