"""
API route definitions.

This module holds FastAPI APIRouter instances. Routers keep endpoints
organized and separate from app setup in main.py.
"""

from fastapi import APIRouter
from pydantic import BaseModel

# Router for public endpoints (root + health checks)
root_router = APIRouter(tags=["root"])

# Router for future REST API endpoints (mounted at /api in main.py)
api_router = APIRouter(tags=["api"])


class RootResponse(BaseModel):
    """Response body for GET /."""

    message: str


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str


@root_router.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    """Confirm the backend is running."""
    return RootResponse(message="AI Job Match Agent Backend Running")


@root_router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Simple health check for monitoring and load balancers."""
    return HealthResponse(status="ok")
