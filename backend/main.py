"""
Application entry point.

Run with: uvicorn main:app --reload
(from the backend directory)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.config  # noqa: F401 — load .env before routes/services use settings
from app.api.routes import api_router, root_router

# Create the FastAPI application instance
app = FastAPI(title="AI Job Match Agent")

# CORS: allow the frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes at / and /health
app.include_router(root_router)

# API namespace at /api — add job-matching routes here later
app.include_router(api_router, prefix="/api")
