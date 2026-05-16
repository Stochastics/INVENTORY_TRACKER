"""FastAPI application entry point for the Inventory MVP backend."""

from fastapi import FastAPI

from app.routes import auth, inventory, items, transactions, users

app = FastAPI(title="Inventory MVP")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(inventory.router)
app.include_router(transactions.router)


@app.get("/health")
def health_check():
    """Return a simple backend health response."""
    return {"status": "ok"}
