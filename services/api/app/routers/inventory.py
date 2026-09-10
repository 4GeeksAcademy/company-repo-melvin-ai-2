"""Register /inventory on the existing FastAPI app (assignment path: routers/inventory.py)."""

from app.inventory.router import router

__all__ = ["router"]
