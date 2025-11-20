"""
CRYPTO VIZ - API Routers
FastAPI routers for modular endpoint organization
"""

from .health import router as health_router

__all__ = ["health_router"]
