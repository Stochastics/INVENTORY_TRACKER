"""FastAPI application entry point for the Inventory MVP backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_tables
from app.routes import auth, inventory, items, transactions, users


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create database tables when the app starts in local development."""
    create_db_tables()
    yield


app = FastAPI(title="Inventory MVP", lifespan=lifespan)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(inventory.router)
app.include_router(transactions.router)
app.include_router(auth.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple backend health response."""
    return {"status": "ok"}
