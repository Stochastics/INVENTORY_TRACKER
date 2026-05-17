"""FastAPI application entry point for the Inventory MVP backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_tables
from app.routes import auth, inventory, items, transactions, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables when the local development app starts."""
    create_db_tables()
    yield


app = FastAPI(title="Inventory MVP", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(inventory.router)
app.include_router(transactions.router)


@app.get("/health")
def health_check():
    """Return a simple backend health response."""
    return {"status": "ok"}
